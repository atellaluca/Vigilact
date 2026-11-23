# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella
"""Reproducible observe -> evaluate -> opt-in authorized capability workflow.

For an isolated demonstration only. Uses local test credentials, a disposable
SQLite database, and TestClient. The reference server executes NO commands.
"""
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from vigilact.server import create_app


class Clock:
    def __init__(self):
        self.at = datetime(2031, 4, 5, 12, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.at


def run_demo():
    credentials = {
        'backup-agent': {'role': 'agent', 'key': 'dev-agent-only-not-for-real-use'},
        'demo-operator': {'role': 'operator', 'key': 'dev-operator-only-not-for-real-use'},
    }
    clock = Clock()
    agent = {'X-Vigilact-Principal': 'backup-agent',
             'X-Vigilact-Key': credentials['backup-agent']['key']}
    operator = {'X-Vigilact-Principal': 'demo-operator',
                'X-Vigilact-Key': credentials['demo-operator']['key']}
    with tempfile.TemporaryDirectory(prefix='vigilact-demo-') as tmp:
        app = create_app(Path(tmp) / 'observer.sqlite3', credentials=credentials,
                         clock=clock, sweep_seconds=0, enable_commands=True)
        with TestClient(app) as api:
            def post(path, data, headers):
                response = api.post(path, json=data, headers=headers)
                response.raise_for_status()
                return response.json()

            proposal = {
                'client_ref': 'nightly-backup', 'subject': 'backup://office-01',
                'observation': {'kind': 'expected_event', 'event_type': 'backup.completed',
                                'deadline_at': (clock.at + timedelta(seconds=30)).isoformat()}}
            contract = post('/v1/contracts', proposal, agent)
            clock.at += timedelta(seconds=31)
            assert app.state.service.evaluate_due() == 1
            state = api.get('/v1/contracts/' + contract['id'], headers=agent).json()
            assert state['outcome'] == 'NOT_OBSERVED'

            events = api.get('/v1/outbox', headers=operator).json()['entries']
            assert len(events) == 1
            assert events[0]['event']['type'] == 'dev.vigilact.observation.not_observed'

            response = api.put('/v1/agents/me/capabilities', headers=agent, json={
                'capabilities': [{'name': 'backup.inspect', 'mode': 'command',
                                  'description': 'Check the most recent backup result',
                                  'invocable': True}]})
            response.raise_for_status()
            command = post('/v1/commands', {
                'request_id': 'investigate-nightly', 'target_agent': 'backup-agent',
                'capability': 'backup.inspect', 'arguments': {'job': 'nightly'}}, operator)
            assert command['status'] == 'PENDING'
            pending = api.get('/v1/agents/me/commands', headers=agent).json()['commands']
            assert len(pending) == 1
            claimed = post('/v1/agents/me/commands/' + command['id'] + '/claim', {}, agent)
            assert claimed['status'] == 'CLAIMED'
            # Only the agent decides whether/how to execute its own allow-listed handler.
            result = post('/v1/agents/me/commands/' + command['id'] + '/result', {
                'status': 'succeeded', 'output': {'diagnosis': 'agent intentionally stopped'}}, agent)
            assert result['status'] == 'SUCCEEDED'
            return {
                'contract_outcome': state['outcome'],
                'observation_event': events[0]['event']['type'],
                'capability': command['capability'],
                'remote_command_execution': 'simulated by agent only',
                'command_state': result['status'],
            }


if __name__ == '__main__':
    print(json.dumps(run_demo(), indent=2))
