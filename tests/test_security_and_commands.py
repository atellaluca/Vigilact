from conftest import event, headers, proposal


def test_authentication_role_scope_and_forged_source(context):
    api, clock, _ = context
    assert api.post("/v1/contracts", json=proposal(clock)).status_code == 401
    assert api.post("/v1/contracts", json=proposal(clock), headers=headers("ops")).status_code == 403
    assert api.get("/v1/outbox", headers=headers()).status_code == 403
    forged = event(agent="node-b")
    response = api.post("/v1/events", json=forged, headers=headers("node-a"))
    assert response.status_code == 403
    assert response.json()["error"] == "source_mismatch"
    hdrs = headers()
    hdrs["X-Vigilact-Key"] = "incorrect"
    assert api.get("/v1/agents/node-a/capabilities", headers=hdrs).status_code == 401
    assert api.get("/v1/agents/node-a/capabilities", headers=headers("node-b")).status_code == 403


def test_opt_in_remote_command_lifecycle_and_idempotence(context):
    api, _, _ = context
    assert api.post("/v1/commands", json={
        "request_id": "cmd-a", "target_agent": "node-a", "capability": "backup.retry"},
        headers=headers("ops")).status_code == 422
    manifest = {"capabilities": [
        {"name": "backup.inspect", "mode": "query"},
        {"name": "backup.retry", "mode": "command", "invocable": True},
        {"name": "system.shutdown", "mode": "command", "invocable": False},
    ]}
    assert api.put("/v1/agents/me/capabilities", json=manifest, headers=headers()).status_code == 200
    cmd = {"request_id": "cmd-a", "target_agent": "node-a",
           "capability": "backup.retry", "arguments": {"job": "nightly"}}
    denied = dict(cmd, request_id="cmd-b", capability="system.shutdown")
    assert api.post("/v1/commands", json=denied, headers=headers("ops")).status_code == 422
    assert api.post("/v1/commands", json=cmd, headers=headers()).status_code == 403
    first = api.post("/v1/commands", json=cmd, headers=headers("ops"))
    assert first.status_code == 201
    queued = first.json()
    assert queued["status"] == "PENDING"
    assert api.post("/v1/commands", json=cmd, headers=headers("ops")).json()["id"] == queued["id"]
    conflicting = dict(cmd, arguments={"job": "different"})
    assert api.post("/v1/commands", json=conflicting, headers=headers("ops")).status_code == 409
    assert len(api.get("/v1/agents/me/commands", headers=headers()).json()["commands"]) == 1
    url = "/v1/agents/me/commands/" + queued["id"]
    assert api.post(url + "/claim", headers=headers("node-b")).status_code == 404
    assert api.post(url + "/result", json={"status": "succeeded"}, headers=headers()).status_code == 409
    claimed = api.post(url + "/claim", headers=headers())
    assert claimed.status_code == 200
    assert claimed.json()["status"] == "CLAIMED"
    assert api.post(url + "/claim", headers=headers()).status_code == 409
    outcome = {"status": "succeeded", "output": {"queued": True}}
    finished = api.post(url + "/result", json=outcome, headers=headers())
    assert finished.json()["status"] == "SUCCEEDED"
    assert api.post(url + "/result", json=outcome, headers=headers()).json()["status"] == "SUCCEEDED"
    assert api.post(url + "/result", json={"status": "failed"}, headers=headers()).status_code == 409
    assert api.get("/v1/agents/me/commands", headers=headers()).json()["commands"] == []


def test_capability_validation(context):
    api, _, _ = context
    duplicate = {"capabilities": [{"name": "backup.retry", "mode": "command"},
                                  {"name": "backup.retry", "mode": "command"}]}
    assert api.put("/v1/agents/me/capabilities", json=duplicate, headers=headers()).status_code == 422
    invalid = {"capabilities": [{"name": "backup.status", "mode": "query", "invocable": True}]}
    assert api.put("/v1/agents/me/capabilities", json=invalid, headers=headers()).status_code == 422
    assert api.get("/v1/agents/node-a/capabilities", headers=headers("ops")).json()["capabilities"] == []


def test_info_and_openapi(context):
    api, _, _ = context
    info = api.get("/v1/info")
    assert info.status_code == 200
    assert "expected_event" in info.json()["profiles"][0]
    assert api.get("/openapi.json").status_code == 200


def test_revoke_capability_cancels_unclaimed_command(context):
    api, _, _ = context
    url = "/v1/agents/me/capabilities"
    manifest = {"capabilities": [{"name": "backup.retry", "mode": "command", "invocable": True}]}
    api.put(url, json=manifest, headers=headers()).raise_for_status()
    request = {"request_id": "cancel-me", "target_agent": "node-a", "capability": "backup.retry"}
    queued = api.post("/v1/commands", json=request, headers=headers("ops")).json()
    api.put(url, json={"capabilities": []}, headers=headers()).raise_for_status()
    assert api.get("/v1/agents/me/commands", headers=headers()).json()["commands"] == []
    assert api.post(f"/v1/agents/me/commands/{queued['id']}/claim", headers=headers()).status_code == 409
    repeated = api.post("/v1/commands", json=request, headers=headers("ops")).json()
    assert repeated["status"] == "CANCELLED"
