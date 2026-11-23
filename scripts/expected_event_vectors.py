# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella
"""Run transport-neutral expected-event vectors against the real Python service.

Usage: PYTHONPATH=src python scripts/expected_event_vectors.py --check
"""
from __future__ import annotations

import argparse
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from vigilact.models import CloudEvent, ContractProposal
from vigilact.service import ProtocolError, VigilactService

ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / 'spec' / 'vectors' / 'expected-event.json'


def run_case(case: dict, fixture: dict) -> dict:
    start = datetime.fromisoformat(fixture['base_time'].replace('Z', '+00:00'))
    current = [start]
    with tempfile.TemporaryDirectory(prefix='vigilact-vector-') as tmp:
        service = VigilactService(Path(tmp) / 'observer.sqlite3', clock=lambda: current[0])
        deadline = start + timedelta(seconds=case['deadline_offset_seconds'])
        accepted = service.create_contract(
            fixture['contract_owner'],
            ContractProposal.model_validate({
                'client_ref': 'vector', 'subject': fixture['subject'],
                'observation': {'kind': 'expected_event',
                                'event_type': fixture['event_type'],
                                'deadline_at': deadline.isoformat()}
            }),
        )
        receipts = []
        for entry in case['events']:
            current[0] = start + timedelta(seconds=entry['offset_seconds'])
            agent = entry.get('agent', fixture['contract_owner'])
            event = {'specversion': '1.0', 'id': entry['id'],
                     'source': entry.get('source', f'urn:vigilact:agent:{agent}'),
                     'type': entry['type'], 'subject': entry['subject'],
                     'data': entry.get('data', {'result': 'ok'})}
            if 'time_offset_seconds' in entry:
                event['time'] = (start + timedelta(seconds=entry['time_offset_seconds'])).isoformat()
            try:
                receipt = service.publish_event(agent, CloudEvent.model_validate(event))
                receipts.append(f"{receipt['status']}:{len(receipt['satisfied_contracts'])}")
            except ProtocolError as exc:
                receipts.append(exc.code)
        current[0] = start + timedelta(seconds=case['evaluate_at_seconds'])
        service.evaluate_due()
        outcome = service.get_contract(accepted['id'], fixture['contract_owner'])['outcome']
        emissions = [row['event']['type'].split('.')[-1] for row in service.read_outbox()['entries']]
        return {'id': case['id'], 'outcome': outcome, 'receipts': receipts, 'emissions': emissions}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Compare results with expected output')
    parser.add_argument('--fixtures', type=Path, default=VECTORS)
    args = parser.parse_args()
    fixture = json.loads(args.fixtures.read_text())
    if fixture['schema'] != 'vigilact.expected-event.vectors/0.1':
        raise SystemExit('Unrecognized fixture schema')
    outputs = [run_case(case, fixture) for case in fixture['cases']]
    if args.check:
        for case, output in zip(fixture['cases'], outputs):
            expected = {'id': case['id'], **case['expected']}
            if output != expected:
                raise SystemExit(f"FAIL {case['id']}: expected={expected!r} actual={output!r}")
        print(f"PASS: {len(outputs)} Python service vectors")
    else:
        print(json.dumps(outputs, indent=2))


if __name__ == '__main__':
    main()
