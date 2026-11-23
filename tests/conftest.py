from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from vigilact.server import create_app


KEYS = {
    "node-a": {"role": "agent", "key": "local-test-node-a-secret-key"},
    "node-b": {"role": "agent", "key": "local-test-node-b-secret-key"},
    "ops": {"role": "operator", "key": "local-test-ops-secret-key--"},
}


def headers(name="node-a"):
    return {"X-Vigilact-Principal": name, "X-Vigilact-Key": KEYS[name]["key"]}


class Clock:
    def __init__(self):
        self.value = datetime(2031, 4, 5, 12, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.value

    def jump(self, *, seconds: int):
        self.value += timedelta(seconds=seconds)


@pytest.fixture()
def context(tmp_path):
    clock = Clock()
    app = create_app(tmp_path / "test.sqlite3", credentials=KEYS,
                     clock=clock, sweep_seconds=0, enable_commands=True)
    with TestClient(app) as client:
        yield client, clock, app


def proposal(clock, ref="backup-1", subject="backup://node-a", offset=60):
    return {
        "client_ref": ref,
        "subject": subject,
        "observation": {
            "kind": "expected_event", "event_type": "backup.completed",
            "deadline_at": (clock.value + timedelta(seconds=offset)).isoformat(),
        },
    }


def event(*, agent="node-a", id="run-1", subject="backup://node-a", data=None):
    return {"specversion": "1.0", "id": id,
            "source": f"urn:vigilact:agent:{agent}",
            "type": "backup.completed", "subject": subject,
            "data": data or {"result": "ok"}}
