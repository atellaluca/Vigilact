from datetime import datetime, timezone

import httpx

from vigilact.client import VigilactClient


def test_sdk_encodes_contract_and_event():
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={"ok": True})

    with VigilactClient("https://example.invalid", "node-a", "super-secret-key-123",
                        transport=httpx.MockTransport(respond)) as client:
        client.propose("job-1", "backup://node", "backup.completed",
                       datetime(2030, 1, 1, tzinfo=timezone.utc))
        client.event("backup://node", "backup.completed", event_id="id-1")
    assert [r.url.path for r in requests] == ["/v1/contracts", "/v1/events"]
    assert all(r.headers["x-vigilact-principal"] == "node-a" for r in requests)
    assert requests[1].read().decode().find('urn:vigilact:agent:node-a') >= 0


def test_sdk_rejects_naive_deadlines():
    with VigilactClient("https://example.invalid", "node-a", "secret-key-is-not-sent") as client:
        try:
            client.propose("x", "subject", "event", datetime(2030, 1, 1))
        except ValueError as exc:
            assert "timezone-aware" in str(exc)
        else:
            raise AssertionError("Should reject naive datetime")
