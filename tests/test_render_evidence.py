# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella
"""Proof reports must fail closed on mismatched/partial evidence."""
import importlib.util
from pathlib import Path
from copy import deepcopy

import pytest

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "render_evidence.py"
spec = importlib.util.spec_from_file_location("render_evidence", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def proof():
    a = {"seed": 12, "cases": 1, "assertions": 1, "semantic_sha256": "abc", "trace": [["ok"]]}
    return {"status": "PASS", "profile": "core.expected_event/0.1",
            "implementations": [
                {"implementation": name, "passed": 1,
                 "checks": [{"test": "demo", "passed": True}],
                 "load_smoke": {"status": "PASS", "transactions": 4},
                 "differential": deepcopy(a)}
                for name in ("python", "go")]}


def test_render_valid_local_proof():
    result = mod.render(proof())
    assert "NOT third-party certification" in result
    assert "| python | 1 | 4 | PASS |" in result
    assert "| go | 1 | 4 | PASS |" in result


def test_reject_divergent_or_unverified_proof():
    p = proof()
    p["implementations"][1]["differential"]["semantic_sha256"] = "different"
    with pytest.raises(ValueError, match="divergent"):
        mod.render(p)
    p = proof()
    p["implementations"][0]["checks"][0]["passed"] = False
    with pytest.raises(ValueError, match="failed"):
        mod.render(p)
    p = proof()
    del p["implementations"][1]["differential"]
    with pytest.raises(ValueError, match="not run"):
        mod.render(p)
