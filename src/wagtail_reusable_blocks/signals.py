"""Signal handlers for ReusableBlock cache invalidation."""

import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .cache import ReusableBlockCache
from .models import ReusableBlock

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ReusableBlock)
def invalidate_cache_on_save(
    sender: type[ReusableBlock],
    instance: ReusableBlock,
    **kwargs: object,
) -> None:
    """Invalidate cache when a ReusableBlock is saved.

    This ensures that any cached rendered content is cleared when the block
    is updated, so the next render will use the updated content.

    Args:
        sender: The ReusableBlock model class
        instance: The ReusableBlock instance that was saved
        **kwargs: Additional signal arguments (created, raw, using, update_fields)
    """
    if not ReusableBlockCache.is_enabled():
        return

    ReusableBlockCache.invalidate(instance.pk)
    logger.debug(
        f"Cache invalidated for ReusableBlock '{instance.name}' (id={instance.pk}) on save"
    )


@receiver(post_delete, sender=ReusableBlock)
def cleanup_cache_on_delete(
    sender: type[ReusableBlock],
    instance: ReusableBlock,
    **kwargs: object,
) -> None:
    """Clean up cache when a ReusableBlock is deleted.

    This removes any cached content for the deleted block to prevent stale
    cache entries.

    Args:
        sender: The ReusableBlock model class
        instance: The ReusableBlock instance that was deleted
        **kwargs: Additional signal arguments (using)
    """
    if not ReusableBlockCache.is_enabled():
        return

    ReusableBlockCache.invalidate(instance.pk)
    logger.debug(
        f"Cache cleaned up for deleted ReusableBlock '{instance.name}' (id={instance.pk})"
    )
