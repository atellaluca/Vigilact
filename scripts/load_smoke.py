#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella
"""Bounded black-box HTTP load smoke; NOT a benchmark or SLA certification.

Usage: python scripts/load_smoke.py --url http://127.0.0.1:8000 --agent dev-agent \
          --agent-key "$VIGILACT_LOAD_AGENT_KEY" --operator dev-ops \
          --operator-key "$VIGILACT_LOAD_OPERATOR_KEY" --count 25
"""
from __future__ import annotations

import argparse
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx


def run(url: str, agent: str, agent_key: str, operator: str, operator_key: str,
        count: int = 25, workers: int = 4) -> dict:
    if not 1 <= count <= 500:
        raise ValueError('count must be 1..500')
    if not 1 <= workers <= 16:
        raise ValueError('workers must be 1..16')
    token = uuid4().hex[:12]
    auth = {'X-Vigilact-Principal': agent, 'X-Vigilact-Key': agent_key}
    operator_auth = {'X-Vigilact-Principal': operator, 'X-Vigilact-Key': operator_key}
    deadline = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    with httpx.Client(base_url=url, timeout=20) as api:
        page = api.get('/v1/outbox', headers=operator_auth)
        page.raise_for_status()
        previous_cursor = page.json()['next_cursor']

    def one(i: int) -> dict:
        subject = f'load://{token}/{i}'
        proposal = {'client_ref': f'load-{token}-{i}', 'subject': subject,
                    'observation': {'kind': 'expected_event', 'event_type': 'load.completed',
                                    'deadline_at': deadline}}
        event = {'specversion': '1.0', 'id': f'load-{token}-{i}',
                 'source': f'urn:vigilact:agent:{agent}', 'type': 'load.completed',
                 'subject': subject, 'data': {'sequence': i}}
        with httpx.Client(base_url=url, timeout=30) as api:
            start = time.perf_counter()
            create = api.post('/v1/contracts', headers=auth, json=proposal)
            create.raise_for_status()
            contract_id = create.json()['id']
            create_elapsed = time.perf_counter() - start
            start = time.perf_counter()
            publish = api.post('/v1/events', headers=auth, json=event)
            publish.raise_for_status()
            if contract_id not in publish.json()['satisfied_contracts']:
                raise AssertionError(f'Contract {contract_id} not satisfied')
            return {'contract_id': contract_id, 'proposal_s': create_elapsed,
                    'event_s': time.perf_counter() - start}

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(one, range(count)))
    elapsed = time.perf_counter() - start
    ids = {r['contract_id'] for r in results}
    actual = set()
    cursor = previous_cursor
    with httpx.Client(base_url=url, timeout=15) as api:
        while len(actual) < count:
            page = api.get('/v1/outbox', params={'after': cursor, 'limit': 500},
                           headers=operator_auth)
            page.raise_for_status()
            data = page.json()
            if not data['entries']:
                break
            for item in data['entries']:
                event = item['event']
                if event['subject'] in ids and event['type'] == 'dev.vigilact.observation.satisfied':
                    actual.add(event['subject'])
            cursor = data['next_cursor']
    if actual != ids:
        raise AssertionError(f'Missing {len(ids - actual)} outbox evaluations')

    def percentile(values: list[float], pct: float) -> float:
        ordered = sorted(values)
        return round(ordered[min(len(ordered) - 1, int((len(ordered) - 1) * pct))] * 1000, 2)

    return {
        'status': 'PASS', 'transactions': count, 'workers': workers,
        'elapsed_seconds': round(elapsed, 3),
        'transactions_per_second_observed': round(count / max(elapsed, 0.000001), 2),
        'proposal_p95_ms': percentile([r['proposal_s'] for r in results], 0.95),
        'event_p95_ms': percentile([r['event_s'] for r in results], 0.95),
        'outbox_evaluations': len(actual),
        'scope': 'bounded local synthetic test; no SLA or production claims',
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--url', required=True)
    ap.add_argument('--agent', required=True)
    ap.add_argument('--agent-key', default=os.environ.get('VIGILACT_LOAD_AGENT_KEY'))
    ap.add_argument('--operator', required=True)
    ap.add_argument('--operator-key', default=os.environ.get('VIGILACT_LOAD_OPERATOR_KEY'))
    ap.add_argument('--count', type=int, default=25)
    ap.add_argument('--workers', type=int, default=4)
    args = ap.parse_args()
    if not args.agent_key or not args.operator_key:
        ap.error('Set agent and operator keys via arguments or environment')
    print(json.dumps(run(args.url, args.agent, args.agent_key, args.operator,
                         args.operator_key, args.count, args.workers), indent=2))


if __name__ == '__main__':
    main()
