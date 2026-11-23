# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella

"""Tiny optional Python HTTP client; uses httpx (install the dev extra for demo)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx


class VigilactClient:
    """Thin transport client. For production, use TLS and provide a trusted URL."""

    def __init__(self, base_url: str, principal: str, key: str,
                 transport: httpx.BaseTransport | None = None) -> None:
        self.principal = principal
        self._client = httpx.Client(base_url=base_url.rstrip("/"), timeout=10,
                                    transport=transport,
                                    headers={"X-Vigilact-Principal": principal,
                                             "X-Vigilact-Key": key})

    def __enter__(self) -> "VigilactClient":
        return self

    def __exit__(self, *_args: object) -> None:
        self._client.close()

    def _send(self, method: str, path: str, **kwargs: Any) -> dict:
        response = self._client.request(method, path, **kwargs)
        response.raise_for_status()
        return response.json()

    def propose(self, client_ref: str, subject: str, event_type: str, deadline_at: datetime) -> dict:
        if deadline_at.tzinfo is None:
            raise ValueError("deadline_at must be timezone-aware")
        return self._send("POST", "/v1/contracts", json={
            "client_ref": client_ref, "subject": subject,
            "observation": {"kind": "expected_event", "event_type": event_type,
                            "deadline_at": deadline_at.astimezone(timezone.utc).isoformat()}})

    def event(self, subject: str, event_type: str, *, event_id: str | None = None,
              data: dict[str, Any] | None = None) -> dict:
        return self._send("POST", "/v1/events", json={
            "specversion": "1.0", "id": event_id or str(uuid4()),
            "source": f"urn:vigilact:agent:{self.principal}",
            "type": event_type, "subject": subject, "data": data or {}})

    def publish_capabilities(self, capabilities: list[dict]) -> dict:
        return self._send("PUT", "/v1/agents/me/capabilities", json={"capabilities": capabilities})

    def pending_commands(self) -> list[dict]:
        return self._send("GET", "/v1/agents/me/commands")["commands"]

    def claim_command(self, command_id: str) -> dict:
        return self._send("POST", f"/v1/agents/me/commands/{command_id}/claim")

    def finish_command(self, command_id: str, success: bool, output: dict | None = None) -> dict:
        return self._send("POST", f"/v1/agents/me/commands/{command_id}/result",
                          json={"status": "succeeded" if success else "failed",
                                "output": output or {}})
