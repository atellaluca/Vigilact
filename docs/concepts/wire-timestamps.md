# Time and timestamp conventions

The experimental `core.expected_event/0.1` HTTP profile accepts **RFC 3339
strings with an explicit timezone** and at most six fractional-second digits.
Both reference observers normalize to UTC and use microsecond precision.

Accepted:

```text
2031-04-05T12:01:00Z
2031-04-05T14:01:00+02:00
2031-04-05T12:01:00.123456Z
```

Rejected:

```text
2031-04-05T12:01:00                  # timezone absent
2031-04-05 12:01:00Z                 # not RFC 3339 T form
2031-04-05T12:01:00.1234567Z        # more than 6 fractional digits
1912353660                          # numeric Unix timestamp
```

An observation is `PENDING` until the server's **receipt time** is strictly
after the declared `deadline_at`. Evidence received *at* the deadline may
satisfy it. A client-supplied CloudEvents `time` is descriptive data only;
it **cannot** backdate receipt or satisfy a late observation. Client and server
clock disagreement can therefore affect the result. Vigilact makes no
wall-clock synchronization guarantee.

The server records an outcome and does not silently rewrite history when a
late event arrives. Use the outbox as an append-only record of *evaluations*,
not as a guarantee that a real-world operation did or did not occur.

See [Evaluation semantics](evaluation-semantics.md) and [Core profile](core-profile.md).
