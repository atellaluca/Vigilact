# Frequently asked questions

## Is Vigilact a notification server?

No. The observer records contract outcomes and emits neutral events. An independent consumer can route them to any notification service. Vigilact and LTG Notify are separate projects with no required dependency.

## Does a missed observation mean the job failed?

No. It means the observer **did not receive the matching evidence by the agreed deadline**. The job may have succeeded while connectivity was unavailable. See [failure semantics](../concepts/failure-semantics.md).

## Can I use cron expressions or threshold conditions?

Not in the implemented alpha profile. Only one-shot `expected_event` contracts with absolute deadlines are supported. Recurrence and thresholds are proposed future extensions.

## Can I use Vigilact with a programming language other than Python?

Yes, HTTP/JSON is language-neutral. A JavaScript client example is included. A Go HTTP Core observer is included and independently passes the shared, limited conformance suite; this does not imply stable or complete interoperability.

## Can the observer execute a command on my device?

The observer can queue a command for an opt-in agent if remote commands are explicitly enabled. It does not execute shell commands itself. Agents must keep a separate local allow-list and validate arguments. Commands are **disabled by default**.

## Does the server need direct inbound access to an agent?

No for the current HTTP binding: agents initiate outbound requests to publish evidence and poll pending commands. This works across common NAT/firewall boundaries subject to network access and policy.

## Is it safe for production use?

No. The reference server is an experimental alpha with static keys, broad operator permissions, no rate limits or tenant isolation, and no distributed high availability. See [security limitations](security.md).

## What license does it use?

The repository includes an Apache-2.0 license. Implementations of the *protocol ideas* do not need to reuse the reference code, and compatible implementations may be independently licensed subject to applicable rights and legal obligations.

## How can I contribute?

Start with [the contributor guide](contributing.md), read [the docs workflow](../maintainers/docs-workflow.md) and propose protocol changes through a GitHub issue before changing externally visible semantics.
