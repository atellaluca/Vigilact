// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 Luca Atella

/**
 * Cross-language client example (Node.js 20+). Uses only built-in fetch.
 * Run against a local development server with:
 * VIGILACT_AGENT_KEY=<your-key> node examples/node_client.mjs
 */
const base = process.env.VIGILACT_URL ?? 'http://127.0.0.1:8000';
const key = process.env.VIGILACT_AGENT_KEY;
const principal = process.env.VIGILACT_AGENT ?? 'backup-agent';
if (!key) throw new Error('Set VIGILACT_AGENT_KEY');

const deadlineAt = new Date(Date.now() + 5 * 60_000).toISOString();
const subject = 'backup://cross-language-example';
const headers = {
  'Content-Type': 'application/json',
  'X-Vigilact-Principal': principal,
  'X-Vigilact-Key': key,
};
async function post(path, body) {
  const r = await fetch(`${base}${path}`, {
    method: 'POST', headers, body: JSON.stringify(body),
  });
  const payload = await r.json();
  if (!r.ok) throw new Error(JSON.stringify(payload));
  return payload;
}

const contract = await post('/v1/contracts', {
  client_ref: `node-example-${crypto.randomUUID()}`,
  subject,
  observation: {kind: 'expected_event', event_type: 'backup.completed', deadline_at: deadlineAt},
});
console.log('Accepted:', contract.id);
const event = await post('/v1/events', {
  specversion: '1.0', id: crypto.randomUUID(),
  source: `urn:vigilact:agent:${principal}`,
  type: 'backup.completed', subject,
  data: {language: 'javascript'},
});
console.log('Evaluated:', event.satisfied_contracts);
