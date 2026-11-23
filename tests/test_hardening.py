"""Security regression and edge-case tests for the HTTP reference binding."""

import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from conftest import KEYS, Clock, event, headers, proposal
from vigilact.http_limits import RequestBodyLimitMiddleware
from vigilact.server import create_app


def test_commands_off_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv("VIGILACT_ENABLE_COMMANDS", raising=False)
    clock = Clock()
    app = create_app(tmp_path / "no_commands.db", credentials=KEYS, clock=clock,
                     sweep_seconds=0)
    with TestClient(app) as client:
        info = client.get("/v1/info").json()
        assert info["features"]["remote_commands"] is False
        assert "agent.commands/0.1" not in info["profiles"]
        for url, method, body, identity in (
            ("/v1/commands", "post", {"request_id": "r", "target_agent": "node-a", "capability": "x"}, "ops"),
            ("/v1/agents/me/commands", "get", None, "node-a"),
            ("/v1/agents/me/commands/missing/claim", "post", None, "node-a"),
            ("/v1/agents/me/commands/missing/result", "post", {"status": "failed"}, "node-a"),
        ):
            response = getattr(client, method)(url, json=body, headers=headers(identity)) if method == "post" else client.get(url, headers=headers(identity))
            assert response.status_code == 403, (url, response.text)
            assert response.json()["error"] == "commands_disabled"


def test_config_rejects_bad_limits_and_boolean(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="1024"):
        create_app(tmp_path / "small.db", credentials=KEYS, max_request_bytes=50)
    monkeypatch.setenv("VIGILACT_ENABLE_COMMANDS", "sometimes")
    with pytest.raises(ValueError, match="VIGILACT_ENABLE_COMMANDS"):
        create_app(tmp_path / "boolean.db", credentials=KEYS)


def test_request_limit_with_content_length(tmp_path):
    app = create_app(tmp_path / "size.db", credentials=KEYS, max_request_bytes=1024,
                     sweep_seconds=0)
    with TestClient(app) as client:
        result = client.post("/v1/events", content=b"x" * 1025,
                             headers={**headers(), "Content-Type": "application/json"})
        assert result.status_code == 413
        assert result.headers["content-type"] == "application/problem+json"
        assert result.json()["error"] == "payload_too_large"


def test_unknown_content_length_is_bounded_by_receive():
    """Exercise the raw ASGI receive path without a Content-Length header."""
    calls = []

    async def echo_app(scope, receive, send):
        while True:
            message = await receive()
            if not message.get("more_body", False):
                break
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    async def perform():
        packets = iter([
            {"type": "http.request", "body": b"a" * 800, "more_body": True},
            {"type": "http.request", "body": b"b" * 800, "more_body": False},
        ])

        async def receive():
            return next(packets)

        async def send(packet):
            calls.append(packet)

        await RequestBodyLimitMiddleware(echo_app, max_bytes=1024)(
            {"type": "http", "headers": [], "method": "POST", "path": "/"}, receive, send)

    asyncio.run(perform())
    assert calls[0]["status"] == 413
    assert json.loads(calls[1]["body"])["error"] == "payload_too_large"


def test_problem_details_do_not_echo_validation_input(context):
    client, clock, _ = context
    sent = proposal(clock)
    sent["observation"]["deadline_at"] = "SECRET-SHOULD-NOT-BE-ECHOED"
    response = client.post("/v1/contracts", json=sent, headers=headers())
    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["status"] == 422
    assert response.json()["error"] == "validation_error"
    assert "SECRET-SHOULD-NOT-BE-ECHOED" not in response.text


def test_exact_deadline_boundary_and_outbox_consistency(context):
    client, clock, _ = context
    contract = client.post("/v1/contracts", json=proposal(clock), headers=headers()).json()
    clock.jump(seconds=60)
    response = client.post("/v1/events", json=event(), headers=headers())
    assert response.json()["satisfied_contracts"] == [contract["id"]]
    assert client.get(f"/v1/contracts/{contract['id']}", headers=headers()).json()["outcome"] == "SATISFIED"
    entries = client.get("/v1/outbox", headers=headers("ops")).json()["entries"]
    assert len(entries) == 1
    assert entries[0]["event"]["type"].endswith("satisfied")


def test_idempotent_contract_after_deadline(context):
    client, clock, _ = context
    data = proposal(clock)
    first = client.post("/v1/contracts", json=data, headers=headers())
    assert first.status_code == 201
    clock.jump(seconds=90)
    # Accepted references are stable even after the deadline has passed.
    second = client.post("/v1/contracts", json=data, headers=headers())
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]


def test_missing_evidence_not_misreported_as_failure(context):
    client, clock, app = context
    ref = client.post("/v1/contracts", json=proposal(clock), headers=headers()).json()["id"]
    clock.jump(seconds=61)
    app.state.service.evaluate_due()
    view = client.get(f"/v1/contracts/{ref}", headers=headers()).json()
    assert view["outcome"] == "NOT_OBSERVED"
    assert "FAILED" not in {view["outcome"], view["state"]}


def test_concurrent_event_retries_emit_only_one_evaluation(context):
    """Independent DB connections must serialize conflicting event retries."""
    from concurrent.futures import ThreadPoolExecutor

    from vigilact.models import CloudEvent

    client, clock, app = context
    ref = client.post("/v1/contracts", json=proposal(clock), headers=headers()).json()["id"]
    evidence = CloudEvent.model_validate(event())
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: app.state.service.publish_event("node-a", evidence),
                                range(12)))
    assert sum(r["status"] == "accepted" for r in results) == 1
    assert sum(r["status"] == "duplicate" for r in results) == 11
    assert sum(ref in r["satisfied_contracts"] for r in results) == 1
    outbox = client.get("/v1/outbox", headers=headers("ops")).json()
    assert len(outbox["entries"]) == 1


def test_readiness_checks_storage(context):
    client, _, app = context
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/readyz").json() == {"status": "ready"}
    assert app.state.service.check_storage() is True
    from pathlib import Path
    Path(app.state.service.db_path).unlink()
    # Liveness and readiness intentionally have different meanings.
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").status_code == 503
