# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella

"""Resource bounds for the experimental HTTP binding.

This deliberately limits streamed bodies rather than trusting Content-Length: a
client is permitted to omit that header when using chunked transfer encoding.
"""

from __future__ import annotations

from starlette.responses import JSONResponse


def _too_large():
    return JSONResponse(
        status_code=413,
        media_type="application/problem+json",
        content={
            "type": "about:blank",
            "title": "Payload Too Large",
            "status": 413,
            "detail": "Request body exceeds the configured size limit",
            "error": "payload_too_large",
        },
    )


class RequestBodyLimitMiddleware:
    """Reject oversized HTTP bodies, including bodies of unknown length."""

    def __init__(self, app, max_bytes: int = 262_144):
        if max_bytes < 1024:
            raise ValueError("max_bytes must be >= 1024")
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        for key, val in scope.get("headers", []):
            if key.lower() == b"content-length":
                try:
                    length = int(val)
                except ValueError:
                    length = self.max_bytes + 1
                if length > self.max_bytes or length < 0:
                    await _too_large()(scope, receive, send)
                    return

        total = 0
        responded = False

        async def bounded_receive():
            nonlocal total
            message = await receive()
            if message.get("type") == "http.request":
                total += len(message.get("body", b""))
                if total > self.max_bytes:
                    raise _LimitExceeded()
            return message

        async def guarded_send(message):
            nonlocal responded
            if message["type"] == "http.response.start":
                responded = True
            await send(message)

        try:
            await self.app(scope, bounded_receive, guarded_send)
        except _LimitExceeded:
            if not responded:
                await _too_large()(scope, receive, send)
            # Once HTTP headers are sent, an error cannot safely become 413;
            # the connection is ended rather than silently accepting the body.


class _LimitExceeded(Exception):
    pass
