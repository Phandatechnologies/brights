"""The signature both sides agree on. A copy of the same file in Phanda Staff OS (integrations/signing.py): keep the two identical.

    message   = "<unix seconds>\\nGET\\n<path>?<query exactly as sent>"
    signature = hex(HMAC-SHA256(shared secret, message))

Sent as the X-Staff-OS-Timestamp and X-Staff-OS-Signature headers. The app refuses anything older than 5 minutes,
so a captured request can't be replayed later. The secret is only ever in environment settings on both sides.
"""

from __future__ import annotations

import hashlib
import hmac

MAX_AGE_SECONDS = 300


def message(ts: int, method: str, path_and_query: str) -> bytes:
    return f"{ts}\n{method.upper()}\n{path_and_query}".encode()


def sign(secret: str, ts: int, method: str, path_and_query: str) -> str:
    return hmac.new(secret.encode(), message(ts, method, path_and_query), hashlib.sha256).hexdigest()


def verify(secret: str, ts_header: str, sig_header: str, method: str, path_and_query: str, now: int) -> bool:
    if not secret or not ts_header.isdigit() or not sig_header:
        return False
    ts = int(ts_header)
    if abs(now - ts) > MAX_AGE_SECONDS:
        return False
    return hmac.compare_digest(sign(secret, ts, method, path_and_query), sig_header)
