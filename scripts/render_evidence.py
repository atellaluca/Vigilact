#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella
"""Render a human-readable report from the black-box Core test JSON.

Refuses to summarize a failed or mismatched behavioral trace.
Generated documents describe test scope, not conformance certification.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def render(record: dict) -> str:
    if record.get("status") != "PASS" or record.get("profile") != "core.expected_event/0.1":
        raise ValueError("Expected a successful experimental Core report")
    implementations = record.get("implementations", [])
    if sorted(i.get("implementation") for i in implementations) != ["go", "python"]:
        raise ValueError("Expected precisely the Python and Go reference observers")
    if not all(all(c.get("passed") is True for c in i.get("checks", [])) for i in implementations):
        raise ValueError("Some named protocol checks failed")
    if not all(i.get("passed") == len(i.get("checks", [])) and i.get("passed", 0) > 0
               for i in implementations):
        raise ValueError("Check count mismatch")
    left, right = (i.get("differential") for i in implementations)
    if not left or not right:
        raise ValueError("Differential tests were not run")
    for obj in (left, right):
        if obj.get("cases", 0) < 1 or obj.get("assertions", 0) < 1:
            raise ValueError("Differential report is empty")
        if len(obj.get("trace", [])) != obj["assertions"]:
            raise ValueError("Differential trace count mismatch")
    if ((left["seed"], left["cases"], left["assertions"], left["semantic_sha256"])
        != (right["seed"], right["cases"], right["assertions"], right["semantic_sha256"])):
        raise ValueError("Independent observers produced divergent results")
    if not all(i.get("load_smoke", {}).get("status") == "PASS" for i in implementations):
        raise ValueError("Expected passing bounded load smoke for each implementation")
    lines = ["# Vigilact — Local engineering verification", "",
             "> Experiment on loopback interfaces, NOT third-party certification, HA validation or an SLA.", "",
             f"**Profile:** `{record['profile']}`  ",
             f"**Seed:** `{left['seed']}`  ",
             f"**Two-agent scenarios per observer:** {left['cases']}  ",
             f"**Canonical behavioral assertions per observer:** {left['assertions']}  ",
             f"**Normalized trace SHA-256 (both):** `{left['semantic_sha256']}`", "",
             "| Observer | HTTP/restart checks | Concurrent contract+event pairs | Result |",
             "|---|---:|---:|---|" ]
    for impl in sorted(implementations, key=lambda x:x["implementation"]):
        n = impl["load_smoke"].get("transactions", 0)
        lines.append(f"| {impl['implementation']} | {impl['passed']} | {n} | PASS |")
    lines.extend(["", "## What was verified", "",
                  "- HTTP authentication, contract proposals, receipt-time evaluation and restart recovery.",
                  "- Isolation of two agents sharing subject/event names, including source spoof rejection.",
                  "- Duplicate event identity and conflicting replay behavior.",
                  "- Exactly one terminal evaluation per satisfied contract in tested traces.",
                  "- Same normalized observable results in both implementations for the selected seed.",
                  "", "## What was NOT verified", "",
                  "- Full protocol equivalence, production security, federation, multi-agent contracts,"
                  " or time-dependent races on real clocks.",
                  "- Network partition resilience, power-loss durability or internet-facing deployments.",
                  "- Production throughput: recorded latency numbers depend on local host and disk.",
                  "", "## Reproduce", "",
                  "```bash",
                  "python -m pytest -q",
                  f"python scripts/test_observers.py --load {implementations[0]['load_smoke']['transactions']} "
                  f"--differential-cases {left['cases']} --seed {left['seed']} \\",
                  "  --report artifacts/core-evidence.json",
                  "python scripts/render_evidence.py artifacts/core-evidence.json --output artifacts/CORE_PROOF.md",
                  "```", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    md = render(json.loads(args.source.read_text(encoding="utf-8")))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(md, encoding="utf-8")
    else:
        print(md)


if __name__ == "__main__":
    main()
