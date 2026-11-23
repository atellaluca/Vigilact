# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella

"""HTTP binding for Vigilact's experimental v0.1 profile."""

from __future__ import annotations

import asyncio
import hmac
import json
import os
import re
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from . import __version__
from .models import (
    CapabilityManifest,
    CloudEvent,
    CommandRequest,
    CommandResult,
    ContractProposal,
    ContractView,
    EventReceipt,
    CapabilityView,
    CommandView,
    CommandList,
    OutboxPage,
)
from .service import ProtocolError, VigilactService
from .http_limits import RequestBodyLimitMiddleware


@dataclass(frozen=True)
class Principal:
    name: str
    role: str


def _credentials_from_env() -> dict[str, dict[str, str]]:
    raw = os.environ.get("VIGILACT_CREDENTIALS_JSON")
    if not raw:
        raise RuntimeError("Set VIGILACT_CREDENTIALS_JSON (no default credentials are provided)")
    parsed = json.loads(raw)
    return parsed


def _validate_credentials(credentials: dict) -> None:
    if not isinstance(credentials, dict) or not credentials:
        raise ValueError("At least one explicit identity is required")
    for name, record in credentials.items():
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", name):
            raise ValueError("Principal names must be 1-64 safe ASCII characters")
        if not isinstance(record, dict) or record.get("role") not in ("agent", "operator"):
            raise ValueError("Each identity must have role agent or operator")
        if not isinstance(record.get("key"), str) or len(record["key"]) < 16:
            raise ValueError("Every identity needs an explicit key of at least 16 characters")


def create_app(
    db_path: str | Path | None = None,
    credentials: dict[str, dict[str, str]] | None = None,
    clock: Callable[[], datetime] | None = None,
    sweep_seconds: float | None = None,
    enable_commands: bool | None = None,
    max_request_bytes: int | None = None,
) -> FastAPI:
    """Create an instance. For demo/test inject credentials and a deterministic clock."""
    identities = credentials if credentials is not None else _credentials_from_env()
    _validate_credentials(identities)
    service = VigilactService(db_path or os.environ.get("VIGILACT_DB_PATH", "./vigilact.sqlite3"), clock)
    interval = sweep_seconds if sweep_seconds is not None else float(os.environ.get("VIGILACT_SWEEP_SECONDS", "5"))
    if interval < 0:
        raise ValueError("sweep_seconds must not be negative")
    if enable_commands is None:
        enabled_value = os.environ.get("VIGILACT_ENABLE_COMMANDS", "false").lower()
        if enabled_value not in {"true", "false", "1", "0"}:
            raise ValueError("VIGILACT_ENABLE_COMMANDS must be true/false or 1/0")
        enable_commands = enabled_value in {"true", "1"}
    body_limit = (max_request_bytes if max_request_bytes is not None
                  else int(os.environ.get("VIGILACT_MAX_REQUEST_BYTES", "262144")))
    if body_limit < 1024:
        raise ValueError("max_request_bytes must be >= 1024")

    async def sweeper() -> None:
        while True:
            await asyncio.sleep(interval)
            await asyncio.to_thread(service.evaluate_due)
            await asyncio.to_thread(service.reconcile_commands)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Reconcile persisted due contracts after process restart.
        await asyncio.to_thread(service.evaluate_due)
        await asyncio.to_thread(service.reconcile_commands)
        task = asyncio.create_task(sweeper()) if interval > 0 else None
        try:
            yield
        finally:
            if task is not None:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task

    app = FastAPI(title="Vigilact Reference Server", version=__version__, lifespan=lifespan)
    app.add_middleware(RequestBodyLimitMiddleware, max_bytes=body_limit)
    app.state.service = service

    def problem(status: int, error: str, detail: str, title: str) -> JSONResponse:
        return JSONResponse(
            status_code=status,
            media_type="application/problem+json",
            content={"type": "about:blank", "title": title, "status": status,
                     "detail": detail, "error": error},
        )

    @app.exception_handler(ProtocolError)
    async def protocol_error_handler(request, exc: ProtocolError):
        return problem(exc.status, exc.code, exc.message, "Protocol error")

    @app.exception_handler(HTTPException)
    async def http_error_handler(request, exc: HTTPException):
        titles = {401: "Unauthorized", 403: "Forbidden", 404: "Not Found"}
        return problem(exc.status_code, "http_error", str(exc.detail),
                       titles.get(exc.status_code, "HTTP error"))

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request, exc: RequestValidationError):
        # Do not echo the supplied request body in the error response.
        return problem(422, "validation_error", "Request validation failed", "Validation error")

    def require_commands() -> None:
        if not enable_commands:
            raise ProtocolError("commands_disabled",
                                "Remote command endpoints are disabled on this server", 403)

    def authenticate(
        x_vigilact_principal: str | None = Header(default=None),
        x_vigilact_key: str | None = Header(default=None),
    ) -> Principal:
        if x_vigilact_principal is None or x_vigilact_key is None:
            raise HTTPException(status_code=401, detail="Missing Vigilact credentials")
        record = identities.get(x_vigilact_principal)
        if record is None or not hmac.compare_digest(record["key"], x_vigilact_key):
            raise HTTPException(status_code=401, detail="Invalid Vigilact credentials")
        return Principal(name=x_vigilact_principal, role=record["role"])

    def require_agent(identity: Principal = Depends(authenticate)) -> Principal:
        if identity.role != "agent":
            raise HTTPException(status_code=403, detail="Agent identity required")
        return identity

    def require_operator(identity: Principal = Depends(authenticate)) -> Principal:
        if identity.role != "operator":
            raise HTTPException(status_code=403, detail="Operator identity required")
        return identity

    @app.get("/healthz", tags=["meta"])
    def healthz():
        return {"status": "ok"}

    @app.get("/readyz", tags=["meta"])
    def readyz():
        if not service.check_storage():
            return JSONResponse(status_code=503, content={"status": "unavailable"})
        return {"status": "ready"}

    @app.get("/v1/info", tags=["meta"])
    def info():
        profiles = ["core.expected_event/0.1", "agent.capabilities/0.1"]
        if enable_commands:
            profiles.append("agent.commands/0.1")
        return {"implementation": "vigilact-python-reference", "version": __version__,
                "protocol": "vigilact/0.1-experimental", "profiles": profiles,
                "features": {"remote_commands": enable_commands,
                             "max_request_bytes": body_limit},
                "transport": "HTTP/JSON", "events": "CloudEvents 1.0 (restricted JSON subset)"}

    @app.post("/v1/contracts", status_code=201, response_model=ContractView, tags=["contracts"])
    def propose_contract(proposal: ContractProposal, identity: Principal = Depends(require_agent)):
        return service.create_contract(identity.name, proposal)

    @app.get("/v1/contracts/{contract_id}", response_model=ContractView, tags=["contracts"])
    def get_contract(contract_id: str, identity: Principal = Depends(authenticate)):
        return service.get_contract(contract_id, identity.name, identity.role == "operator")

    @app.post("/v1/events", response_model=EventReceipt, tags=["events"])
    def publish_event(event: CloudEvent, identity: Principal = Depends(require_agent)):
        return service.publish_event(identity.name, event)

    @app.get("/v1/outbox", response_model=OutboxPage, tags=["events"])
    def list_outbox(after: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                    identity: Principal = Depends(require_operator)):
        return service.read_outbox(after, limit)

    @app.put("/v1/agents/me/capabilities", response_model=CapabilityView, tags=["capabilities"])
    def put_capabilities(body: CapabilityManifest, identity: Principal = Depends(require_agent)):
        return service.put_capabilities(identity.name, body)

    @app.get("/v1/agents/{agent}/capabilities", response_model=CapabilityView, tags=["capabilities"])
    def get_capabilities(agent: str, identity: Principal = Depends(authenticate)):
        if identity.role != "operator" and identity.name != agent:
            raise HTTPException(status_code=403, detail="Access denied")
        return service.read_capabilities(agent)

    @app.post("/v1/commands", status_code=201, response_model=CommandView, tags=["commands"])
    def queue_command(body: CommandRequest, identity: Principal = Depends(require_operator)):
        require_commands()
        return service.enqueue_command(identity.name, body)

    @app.get("/v1/commands/{command_id}", response_model=CommandView, tags=["commands"])
    def get_command(command_id: str, identity: Principal = Depends(require_operator)):
        require_commands()
        return service.get_command(identity.name, command_id)

    @app.get("/v1/agents/me/commands", response_model=CommandList, tags=["commands"])
    def commands_for_agent(identity: Principal = Depends(require_agent)):
        require_commands()
        return {"commands": service.pending_commands(identity.name)}

    @app.post("/v1/agents/me/commands/{command_id}/claim", response_model=CommandView, tags=["commands"])
    def claim_command(command_id: str, identity: Principal = Depends(require_agent)):
        require_commands()
        return service.claim_command(identity.name, command_id)

    @app.post("/v1/agents/me/commands/{command_id}/result", response_model=CommandView, tags=["commands"])
    def resolve_command(command_id: str, result: CommandResult,
                        identity: Principal = Depends(require_agent)):
        require_commands()
        return service.resolve_command(identity.name, command_id, result)

    return app
