"""High-level cache service used by the Orchestrator.

Responsibilities
----------------
* Normalise (source, query) → a stable cache key (SHA-256 hex digest).
* Wrap CacheBackend.get / .set with TTL logic from Settings.
* Provide a no-op bypass when --no-cache is active.
"""

from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timezone
from typing import Optional

from src.config import Settings
from src.models import CacheEntry
from src.storage.cache_store import CacheBackend

logger = logging.getLogger(__name__)


def _normalise_query(query: str) -> str:
    """Return a canonical form of *query* for use as a cache key component.

    Strips leading/trailing whitespace, lowercases, collapses internal spaces.
    """
    return " ".join(query.strip().lower().split())


def _make_key(source: str, query: str) -> str:
    """Return a SHA-256 hex digest for the (source, normalised_query) pair.

    Using a hash keeps file names short and filesystem-safe.
    """
    canonical = f"{source.strip().lower()}::{_normalise_query(query)}"
    return hashlib.sha256(canonical.encode()).hexdigest()


class CacheService:
    """Facade over CacheBackend that adds TTL management and key derivation.

    Parameters
    ----------
    backend:
        The storage backend (FilesystemCache or InMemoryCache).
    settings:
        Application settings (provides cache_ttl_seconds).
    enabled:
        When False every ``get`` returns None and every ``set`` is a no-op.
        Pass ``enabled=False`` for ``--no-cache`` CLI flag.
    """

    def __init__(
        self,
        backend: CacheBackend,
        settings: Settings,
        *,
        enabled: bool = True,
    ) -> None:
        self._backend = backend
        self._settings = settings
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        """Whether source cache reads and writes are active."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    # ── public API ────────────────────────────────────────────────────────────

    def get(self, source: str, query: str) -> Optional[CacheEntry]:
        """Look up a cached entry.

        Returns None if the cache is disabled, the key is absent, or the
        entry has expired.
        """
        if not self._enabled:
            return None
        key = _make_key(source, query)
        entry = self._backend.get(key)
        if entry is not None:
            logger.info("Cache HIT  source=%s query=%r", source, query)
        else:
            logger.debug("Cache MISS source=%s query=%r", source, query)
        return entry

    def set(self, source: str, query: str, entry: CacheEntry) -> None:
        """Store an entry.  No-op when cache is disabled."""
        if not self._enabled:
            return
        ttl = self._settings.cache_ttl_seconds
        now = datetime.now(timezone.utc).timestamp()
        expires_at = (now + ttl) if ttl > 0 else 0.0

        # Patch the entry with the correct expiry before storing.
        patched = entry.model_copy(update={"expires_at": expires_at})
        key = _make_key(source, query)
        self._backend.set(key, patched)
        logger.info("Cache SET  source=%s query=%r ttl=%ds", source, query, ttl)

    def invalidate(self, source: str, query: str) -> None:
        """Remove a specific entry (e.g. after a forced refresh)."""
        if not self._enabled:
            return
        key = _make_key(source, query)
        self._backend.delete(key)

    def clear_all(self) -> None:
        """Wipe the entire cache."""
        self._backend.clear()
        logger.info("Cache cleared")
