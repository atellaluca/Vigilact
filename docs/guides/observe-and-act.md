# Observe, then act — with explicit permission

A missing operational event is not equivalent to a failed action. Vigilact
records what the observer can demonstrate. It can then expose a *separate*
mechanism for an operator to request an agent-owned diagnostic capability.

Run a deterministic, fully isolated example:

```bash
PYTHONPATH=src python examples/observe_and_act.py
```

The example:

1. Proposes a deadline-bound `backup.completed` contract.
2. Advances a test clock beyond the deadline without delivering the evidence.
3. Verifies that the observer emits `dev.vigilact.observation.not_observed`.
4. Registers an **opt-in** agent command capability `backup.inspect`.
5. Lets an authenticated operator enqueue a request.
6. Shows the agent claiming and returning a *simulated* diagnostic result.

The server never executes arbitrary commands. **Remote command APIs are
disabled by default**; the demo explicitly enables them only inside an
isolated FastAPI test instance with disposable credentials and database.

This is the minimum meaningful difference between observing a missed ping and
coordinating optional authorized diagnostics. It does **not** implement a
production permissions system or automate remediation.

Related: [Capabilities](../protocol/capabilities.md),
[Commands](../protocol/commands.md), and
[Identity and trust](../concepts/trust.md).
