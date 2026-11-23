# SPDX-License-Identifier: Apache-2.0
"""The real persisted service MUST match the published expected-event vectors."""
import json
import runpy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / 'spec/vectors/expected-event.json').read_text())
RUN_CASE = runpy.run_path(str(ROOT / 'scripts/expected_event_vectors.py'))['run_case']


@pytest.mark.parametrize('case', FIXTURE['cases'], ids=lambda c: c['id'])
def test_expected_event_wire_semantics(case):
    actual = RUN_CASE(case, FIXTURE)
    assert actual == {'id': case['id'], **case['expected']}


def test_vector_fixture_valid_against_public_schema():
    schema = json.loads((ROOT / 'schemas/expected-event-vectors.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(FIXTURE)
    assert len({case['id'] for case in FIXTURE['cases']}) == len(FIXTURE['cases'])
    for case in FIXTURE['cases']:
        offsets = [event['offset_seconds'] for event in case['events']]
        assert offsets == sorted(offsets), case['id']
        assert not offsets or case['evaluate_at_seconds'] >= offsets[-1], case['id']
