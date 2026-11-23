from conftest import event, headers, proposal


def test_contract_acceptance_and_idempotence(context):
    client, clock, _ = context
    body = proposal(clock)
    first = client.post("/v1/contracts", json=body, headers=headers())
    assert first.status_code == 201
    accepted = first.json()
    assert accepted["state"] == "ACTIVE" and accepted["outcome"] == "PENDING"
    repeated = client.post("/v1/contracts", json=body, headers=headers())
    assert repeated.status_code == 201
    assert repeated.json()["id"] == accepted["id"]
    body["observation"]["event_type"] = "backup.failed"
    conflict = client.post("/v1/contracts", json=body, headers=headers())
    assert conflict.status_code == 409
    assert conflict.json()["error"] == "reference_conflict"


def test_event_satisfies_and_deduplicates(context):
    client, clock, app = context
    contract = client.post("/v1/contracts", json=proposal(clock), headers=headers()).json()
    result = client.post("/v1/events", json=event(), headers=headers())
    assert result.status_code == 200
    assert result.json()["satisfied_contracts"] == [contract["id"]]
    duplicate = client.post("/v1/events", json=event(), headers=headers())
    assert duplicate.json() == {"status": "duplicate", "satisfied_contracts": []}
    modified = client.post("/v1/events", json=event(data={"result": "different"}), headers=headers())
    assert modified.status_code == 409
    clock.jump(seconds=120)
    assert app.state.service.evaluate_due() == 0
    state = client.get("/v1/contracts/" + contract["id"], headers=headers()).json()
    assert state["outcome"] == "SATISFIED"
    outbox = client.get("/v1/outbox", headers=headers("ops")).json()
    assert len(outbox["entries"]) == 1
    assert outbox["entries"][0]["event"]["type"] == "dev.vigilact.observation.satisfied"


def test_missed_deadline_late_evidence_and_outbox_cursor(context):
    client, clock, app = context
    contract = client.post("/v1/contracts", json=proposal(clock), headers=headers()).json()
    clock.jump(seconds=61)
    assert app.state.service.evaluate_due() == 1
    assert app.state.service.evaluate_due() == 0
    late = client.post("/v1/events", json=event(), headers=headers()).json()
    assert late["satisfied_contracts"] == []
    assert client.get("/v1/contracts/" + contract["id"], headers=headers()).json()["outcome"] == "NOT_OBSERVED"
    first = client.get("/v1/outbox?after=0&limit=1", headers=headers("ops")).json()
    assert len(first["entries"]) == 1
    seq = first["next_cursor"]
    assert client.get(f"/v1/outbox?after={seq}", headers=headers("ops")).json()["entries"] == []


def test_event_after_deadline_auto_marks_missing_before_ingestion(context):
    client, clock, _ = context
    contract = client.post("/v1/contracts", json=proposal(clock), headers=headers()).json()
    clock.jump(seconds=65)
    response = client.post("/v1/events", json=event(), headers=headers()).json()
    assert response["satisfied_contracts"] == []
    assert client.get("/v1/contracts/" + contract["id"], headers=headers()).json()["outcome"] == "NOT_OBSERVED"


def test_cross_agent_not_allowed_to_satisfy_another_contract(context):
    client, clock, _ = context
    body = proposal(clock)
    contract = client.post("/v1/contracts", json=body, headers=headers()).json()
    other = event(agent="node-b")
    assert client.post("/v1/events", json=other, headers=headers("node-b")).json()["satisfied_contracts"] == []
    assert client.get("/v1/contracts/" + contract["id"], headers=headers()).json()["outcome"] == "PENDING"
    assert client.get("/v1/contracts/" + contract["id"], headers=headers("node-b")).status_code == 404


def test_malformed_deadline_and_past_contract_rejected(context):
    client, clock, _ = context
    body = proposal(clock)
    body["observation"]["deadline_at"] = "2031-04-05T12:01:00"
    assert client.post("/v1/contracts", json=body, headers=headers()).status_code == 422
    body = proposal(clock, offset=-1)
    assert client.post("/v1/contracts", json=body, headers=headers()).status_code == 422


def test_restart_recovers_due_contract(tmp_path):
    from fastapi.testclient import TestClient
    from vigilact.server import create_app
    from conftest import Clock, KEYS
    clock = Clock()
    path = tmp_path / "restart.db"
    with TestClient(create_app(path, credentials=KEYS, clock=clock, sweep_seconds=0)) as api:
        contract = api.post("/v1/contracts", json=proposal(clock), headers=headers()).json()
    clock.jump(seconds=90)
    with TestClient(create_app(path, credentials=KEYS, clock=clock, sweep_seconds=0)) as api:
        assert api.get("/v1/contracts/" + contract["id"], headers=headers()).json()["outcome"] == "NOT_OBSERVED"
        assert len(api.get("/v1/outbox", headers=headers("ops")).json()["entries"]) == 1
