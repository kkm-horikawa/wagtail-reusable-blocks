"""Caching utilities for ReusableBlock rendering."""

import hashlib
import json
import logging
from typing import Any

from django.core.cache import caches
from django.core.cache.backends.base import BaseCache

from .conf import get_setting

logger = logging.getLogger(__name__)


class ReusableBlockCache:
    """Cache manager for ReusableBlock rendered content.

    Provides caching functionality for ReusableBlock and ReusableLayoutBlock
    rendering to improve performance on pages with multiple reusable blocks.

    Cache keys are generated based on:
    - Block ID
    - Slot content hash (for ReusableLayoutBlock)

    Usage:
        >>> from wagtail_reusable_blocks.cache import ReusableBlockCache
        >>>
        >>> # Check cache
        >>> cached = ReusableBlockCache.get(block_id=123)
        >>> if cached is not None:
        ...     return cached
        >>>
        >>> # Render and cache
        >>> rendered = block.render()
        >>> ReusableBlockCache.set(block_id=123, content=rendered)

    Configuration:
        In settings.py:
        >>> WAGTAIL_REUSABLE_BLOCKS = {
        ...     'CACHE_ENABLED': True,
        ...     'CACHE_BACKEND': 'default',
        ...     'CACHE_TIMEOUT': 3600,
        ...     'CACHE_PREFIX': 'wrb:',
        ... }
    """

    @classmethod
    def is_enabled(cls) -> bool:
        """Check if caching is enabled.

        Returns:
            True if caching is enabled, False otherwise
        """
        return bool(get_setting("CACHE_ENABLED"))

    @classmethod
    def get_cache(cls) -> BaseCache:
        """Get the configured cache backend.

        Returns:
            Django cache backend instance
        """
        backend_name = get_setting("CACHE_BACKEND")
        return caches[backend_name]

    @classmethod
    def get_prefix(cls) -> str:
        """Get the cache key prefix.

        Returns:
            Cache key prefix string
        """
        prefix: str = get_setting("CACHE_PREFIX")
        return prefix

    @classmethod
    def get_timeout(cls) -> int:
        """Get the cache timeout in seconds.

        Returns:
            Cache timeout in seconds
        """
        timeout: int = get_setting("CACHE_TIMEOUT")
        return timeout

    @classmethod
    def get_cache_key(
        cls,
        block_id: int,
        slot_content: list[dict[str, Any]] | None = None,
    ) -> str:
        """Generate a unique cache key for a block.

        Args:
            block_id: The ReusableBlock primary key
            slot_content: Optional slot content for ReusableLayoutBlock

        Returns:
            Cache key string

        Example:
            >>> ReusableBlockCache.get_cache_key(123)
            'wrb:123'
            >>> ReusableBlockCache.get_cache_key(123, [{'slot_id': 'main', ...}])
            'wrb:123:a1b2c3d4'
        """
        prefix = cls.get_prefix()
        key = f"{prefix}{block_id}"

        if slot_content:
            # Generate hash from slot content for unique key
            content_json = json.dumps(
                slot_content,
                sort_keys=True,
                default=str,  # Handle non-serializable objects
            )
            content_hash = hashlib.md5(
                content_json.encode(),
                usedforsecurity=False,
            ).hexdigest()[:8]
            key = f"{key}:{content_hash}"

        return key

    @classmethod
    def get(
        cls,
        block_id: int,
        slot_content: list[dict[str, Any]] | None = None,
    ) -> str | None:
        """Get cached rendered content for a block.

        Args:
            block_id: The ReusableBlock primary key
            slot_content: Optional slot content for ReusableLayoutBlock

        Returns:
            Cached rendered content, or None if not cached
        """
        if not cls.is_enabled():
            return None

        key = cls.get_cache_key(block_id, slot_content)
        cache = cls.get_cache()
        cached: str | None = cache.get(key)

        if cached is not None:
            logger.debug(f"Cache hit for ReusableBlock {block_id} (key={key})")
        else:
            logger.debug(f"Cache miss for ReusableBlock {block_id} (key={key})")

        return cached

    @classmethod
    def set(
        cls,
        block_id: int,
        content: str,
        slot_content: list[dict[str, Any]] | None = None,
        timeout: int | None = None,
    ) -> None:
        """Cache rendered content for a block.

        Args:
            block_id: The ReusableBlock primary key
            content: Rendered HTML content to cache
            slot_content: Optional slot content for ReusableLayoutBlock
            timeout: Optional custom timeout (uses default if not specified)
        """
        if not cls.is_enabled():
            return

        key = cls.get_cache_key(block_id, slot_content)
        cache = cls.get_cache()
        cache_timeout = timeout if timeout is not None else cls.get_timeout()

        cache.set(key, content, cache_timeout)
        logger.debug(
            f"Cached ReusableBlock {block_id} (key={key}, timeout={cache_timeout}s)"
        )

    @classmethod
    def delete(
        cls,
        block_id: int,
        slot_content: list[dict[str, Any]] | None = None,
    ) -> None:
        """Delete cached content for a specific block/slot combination.

        Args:
            block_id: The ReusableBlock primary key
            slot_content: Optional slot content for ReusableLayoutBlock
        """
        key = cls.get_cache_key(block_id, slot_content)
        cache = cls.get_cache()
        cache.delete(key)
        logger.debug(f"Deleted cache for ReusableBlock {block_id} (key={key})")

    @classmethod
    def invalidate(cls, block_id: int) -> None:
        """Invalidate all cache entries for a block.

        This uses cache versioning by deleting the base key.
        Note: This only deletes the exact key, not pattern-based entries.
        For full invalidation of layout variants, consider using cache versioning.

        Args:
            block_id: The ReusableBlock primary key
        """
        # Delete the base cache entry (without slot content)
        cls.delete(block_id)
        logger.debug(f"Invalidated cache for ReusableBlock {block_id}")

    @classmethod
    def clear_all(cls) -> None:
        """Clear all ReusableBlock cache entries.

        Warning: This clears the entire cache backend, not just ReusableBlock entries.
        Use with caution in production.
        """
        cache = cls.get_cache()
        cache.clear()
        logger.info("Cleared all cache entries")
