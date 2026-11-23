# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella
"""Keep the published HTTP walkthrough executable as code evolves."""
import asyncio
import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import httpx

from vigilact.server import create_app


async def _exercise(tmp_path):
    module_path = Path(__file__).resolve().parents[1] / "examples" / "http_contract_demo.py"
    spec = importlib.util.spec_from_file_location("http_contract_demo", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    credentials = {
        "example-agent": {"role": "agent", "key": "example-agent-key-strong-12345"},
        "example-ops": {"role": "operator", "key": "example-operator-key-strong-12345"},
    }
    clock = lambda: datetime(2030, 2, 3, 12, 0, tzinfo=timezone.utc)
    app = create_app(db_path=tmp_path / "example.sqlite3", credentials=credentials,
                     clock=clock, sweep_seconds=0)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                 base_url="http://local-test") as client:
        result = await module.walkthrough(client, agent="example-agent",
                                          agent_key=credentials["example-agent"]["key"],
                                          operator="example-ops",
                                          operator_key=credentials["example-ops"]["key"],
                                          now=clock())
        assert result["outcome"] == "SATISFIED"
        assert result["event_type"] == "dev.vigilact.observation.satisfied"
        assert result["outbox_sequence"] == "1"


def test_documentation_http_walkthrough(tmp_path):
    asyncio.run(_exercise(tmp_path))
