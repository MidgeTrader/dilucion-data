"""Shared HTTP connection pool for all API clients.

Avoids creating a new httpx.Client() per request, which leaks file descriptors
on macOS under concurrent load. Use get_client() wherever you'd write
``with httpx.Client(timeout=N) as client:``.

IMPORTANT: default timeouts are deliberately short (connect=5s, read=15s).
Longer defaults caused cascading failures when DNS resolution failed — every
hung connection consumed a pool slot AND a file descriptor until the 30s
timeout expired, leading to ``OSError: [Errno 24] Too many open files``.
"""

from __future__ import annotations

import logging
from typing import Optional, Union

import httpx

logger = logging.getLogger(__name__)

# Default pool limits — keep within macOS fd budget.
# 10 connections is generous for serial API calls; httpx also keeps
# keepalive connections open, so we keep the pool small.
_DEFAULT_LIMITS = httpx.Limits(
    max_keepalive_connections=5,
    max_connections=10,
    keepalive_expiry=30.0,
)

# Default timeout: connect 5s (DNS + TCP handshake), read 15s (response body).
# Keep total < 20s so a flaky upstream doesn't cascade into fd exhaustion.
_DEFAULT_TIMEOUT = httpx.Timeout(
    connect=5.0,
    read=15.0,
    write=10.0,
    pool=5.0,
)

# Cached clients keyed by (timeout_tuple, follow_redirects, frozenset(headers))
_clients: dict[tuple, httpx.Client] = {}


def _limits_tuple(limits: httpx.Limits) -> tuple:
    """Convert httpx.Limits to a hashable tuple for cache keys."""
    return (limits.max_keepalive_connections, limits.max_connections,
            limits.keepalive_expiry)


def _timeout_tuple(timeout: httpx.Timeout) -> tuple:
    """Convert httpx.Timeout to a hashable tuple for cache keys."""
    return (timeout.connect, timeout.read, timeout.write, timeout.pool)


def get_client(
    timeout: Optional[Union[float, httpx.Timeout]] = None,
    headers: Optional[dict[str, str]] = None,
    limits: Optional[httpx.Limits] = None,
    follow_redirects: bool = False,
) -> httpx.Client:
    """Return a shared, pool-limited httpx.Client.

    Clients are cached by configuration so callers with the same parameters
    reuse the same connection pool.  You do NOT need to call ``.close()`` or
    use a ``with`` block — the client lives for the lifetime of the process.

    Args:
        timeout: Default 5s connect + 15s read. Pass a float for backward
            compatibility (sets all phases). Pass httpx.Timeout for granular
            control.
        headers: Optional default headers.
        limits: Connection pool limits.
        follow_redirects: Whether to follow redirects.
    """
    resolved_timeout: httpx.Timeout
    if timeout is None:
        resolved_timeout = _DEFAULT_TIMEOUT
    elif isinstance(timeout, httpx.Timeout):
        resolved_timeout = timeout
    else:
        # Backward compat: float → httpx.Timeout
        resolved_timeout = httpx.Timeout(timeout)

    resolved_limits = limits or _DEFAULT_LIMITS
    key = (
        _timeout_tuple(resolved_timeout),
        follow_redirects,
        frozenset((headers or {}).items()),
        _limits_tuple(resolved_limits),
    )
    if key not in _clients:
        _clients[key] = httpx.Client(
            timeout=resolved_timeout,
            headers=headers,
            limits=resolved_limits,
            follow_redirects=follow_redirects,
        )
        logger.debug("Created new httpx.Client pool (timeout=%s)", resolved_timeout)
    return _clients[key]
