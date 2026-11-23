# SPDX-License-Identifier: Apache-2.0
import runpy
from pathlib import Path


def test_observe_and_act_example():
    path = Path(__file__).resolve().parents[1] / 'examples/observe_and_act.py'
    summary = runpy.run_path(str(path))['run_demo']()
    assert summary['contract_outcome'] == 'NOT_OBSERVED'
    assert summary['command_state'] == 'SUCCEEDED'
    assert summary['remote_command_execution'] == 'simulated by agent only'
