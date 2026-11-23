# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella
"""Black-box publication gate: two independent HTTP observers, same protocol checks.

Builds the Go observer, starts each implementation as a local process, exercises
HTTP conformance, restarts it with the same storage, checks recovery of an overdue
contract, and rejects late evidence. No production infrastructure or network access.

Usage: python scripts/test_observers.py
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from conformance_http import run as conformance_run
from load_smoke import run as load_run
from differential_core import run as differential_run

ROOT = Path(__file__).resolve().parents[1]
AGENT = "ci-agent"
SECOND_AGENT = "ci-agent-b"
SECOND_AGENT_KEY = "ci-ephemeral-secondary-agent-key-987654321"
OPERATOR = "ci-operator"
AGENT_KEY = "ci-ephemeral-agent-test-key-123456789"
OPERATOR_KEY = "ci-ephemeral-ops-test-key-123456789"
CREDENTIALS = json.dumps({
    AGENT: {"role": "agent", "key": AGENT_KEY},
    SECOND_AGENT: {"role": "agent", "key": SECOND_AGENT_KEY},
    OPERATOR: {"role": "operator", "key": OPERATOR_KEY},
})
AGENT_HEADERS = {"X-Vigilact-Principal": AGENT, "X-Vigilact-Key": AGENT_KEY}
OPS_HEADERS = {"X-Vigilact-Principal": OPERATOR, "X-Vigilact-Key": OPERATOR_KEY}


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def start(command: list[str], env: dict[str, str], log_path: Path):
    logfile = log_path.open("ab")
    try:
        proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=logfile, stderr=subprocess.STDOUT)
    finally:
        logfile.close()
    return proc


def stop(proc: subprocess.Popen):
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=7)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def wait_healthy(url: str, proc: subprocess.Popen, log_path: Path):
    for _ in range(100):
        if proc.poll() is not None:
            raise RuntimeError(f"Server stopped unexpectedly: {log_path.read_text()[-2500:]}")
        try:
            if httpx.get(url + "/readyz", timeout=0.5).status_code == 200:
                return
        except (httpx.ConnectError, httpx.TimeoutException):
            pass
        time.sleep(0.1)
    raise RuntimeError(f"Server not ready: {log_path.read_text()[-2500:]}")


def run_server(name: str, command_factory, env_factory, suffix: str, work: Path,
               load_count: int = 0, differential_cases: int = 0, seed: int = 20261123) -> dict:
    port = free_port()
    url = f"http://127.0.0.1:{port}"
    db = work / (name + suffix)
    logfile = work / (name + ".log")
    env = env_factory(db)
    command = command_factory(port, db)
    proc = start(command, env, logfile)
    try:
        wait_healthy(url, proc, logfile)
        steps = conformance_run(url, AGENT, AGENT_KEY, OPERATOR, OPERATOR_KEY)
        with httpx.Client(base_url=url, timeout=5) as api:
            previous = api.get("/v1/outbox", headers=OPS_HEADERS).json()["next_cursor"]
            deadline = datetime.now(timezone.utc) + timedelta(seconds=2)
            marker = "restart-" + name
            proposed = {
                "client_ref": marker,
                "subject": "recovery://" + marker,
                "observation": {"kind": "expected_event", "event_type": "recovery.completed",
                                "deadline_at": deadline.isoformat()},
            }
            response = api.post("/v1/contracts", headers=AGENT_HEADERS, json=proposed)
            assert response.status_code == 201, response.text
            contract_id = response.json()["id"]
        stop(proc)
        # Restart after the agreed deadline, forcing recovery from durable state.
        time.sleep(max(0, (deadline - datetime.now(timezone.utc)).total_seconds() + 0.25))
        proc = start(command, env, logfile)
        wait_healthy(url, proc, logfile)
        with httpx.Client(base_url=url, timeout=5) as api:
            contract = api.get("/v1/contracts/" + contract_id, headers=AGENT_HEADERS)
            assert contract.status_code == 200 and contract.json()["outcome"] == "NOT_OBSERVED", contract.text
            steps.append({"test": "restart recovers overdue contract", "passed": True})
            page = api.get(f"/v1/outbox?after={previous}", headers=OPS_HEADERS)
            assert page.status_code == 200
            events = [e["event"] for e in page.json()["entries"] if e["event"]["subject"] == contract_id]
            assert len(events) == 1 and events[0]["type"] == "dev.vigilact.observation.not_observed"
            steps.append({"test": "restart produces one durable missing-event outcome", "passed": True})
            late = {
                "specversion": "1.0", "id": "late-" + marker,
                "source": f"urn:vigilact:agent:{AGENT}",
                "type": "recovery.completed", "subject": proposed["subject"], "data": {"late": True},
            }
            response = api.post("/v1/events", json=late, headers=AGENT_HEADERS)
            assert response.status_code == 200 and not response.json()["satisfied_contracts"], response.text
            steps.append({"test": "late evidence does not satisfy resolved contract", "passed": True})
            again = api.get(f"/v1/outbox?after={previous}", headers=OPS_HEADERS).json()
            assert len([e for e in again["entries"] if e["event"]["subject"] == contract_id]) == 1
            steps.append({"test": "late evidence does not duplicate evaluation", "passed": True})
        result = {"implementation": name, "passed": len(steps), "checks": steps}
        if differential_cases:
            result["differential"] = differential_run(
                url, seed=seed, cases=differential_cases,
                agents={AGENT: AGENT_KEY, SECOND_AGENT: SECOND_AGENT_KEY},
                operator=(OPERATOR, OPERATOR_KEY))
        if load_count:
            result["load_smoke"] = load_run(url, AGENT, AGENT_KEY, OPERATOR, OPERATOR_KEY,
                                             count=load_count)
        return result
    finally:
        stop(proc)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--load", type=int, default=0,
                    help="Also run a bounded concurrent HTTP load smoke (e.g. 25)")
    ap.add_argument("--differential-cases", type=int, default=0,
                    help="Run seeded two-agent black-box differential scenarios (e.g. 12)")
    ap.add_argument("--seed", type=int, default=20261123)
    ap.add_argument("--report", help="Write JSON evidence to this path on success")
    args = ap.parse_args()
    if not 0 <= args.differential_cases <= 100:
        ap.error("--differential-cases must be 0..100")
    if args.load < 0 or args.load > 500:
        ap.error("--load must be 0..500")
    with tempfile.TemporaryDirectory(prefix="vigilact-two-servers-") as tmp:
        work = Path(tmp)
        go_binary = work / "vigilact-go-observer"
        subprocess.run(["go", "build", "-o", str(go_binary), "."],
                       cwd=ROOT / "implementations" / "go-observer", check=True)
        def env_for(db):
            return {**os.environ, "VIGILACT_CREDENTIALS_JSON": CREDENTIALS,
                    "VIGILACT_DB_PATH": str(db), "VIGILACT_SWEEP_SECONDS": "0"}
        python_result = run_server(
            "python", lambda port, db: [sys.executable, "-m", "uvicorn",
                                          "vigilact.server:create_app", "--factory", "--host", "127.0.0.1",
                                          "--port", str(port)], env_for, ".sqlite3", work, args.load, args.differential_cases, args.seed)
        go_result = run_server(
            "go", lambda port, db: [str(go_binary), "--addr", f"127.0.0.1:{port}", "--db", str(db)],
            env_for, ".json", work, args.load, args.differential_cases, args.seed)
        if args.differential_cases:
            a = python_result["differential"]
            b = go_result["differential"]
            assert a["semantic_sha256"] == b["semantic_sha256"], "Observers diverged under the same seed"
        report = {"profile": "core.expected_event/0.1", "status": "PASS",
                  "method": "bounded, local black-box verification, NOT production certification",
                  "implementations": [python_result, go_result]}
        if args.report:
            report_path = Path(args.report)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
