"""Django app configuration for wagtail-reusable-blocks."""

import logging

from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class WagtailReusableBlocksConfig(AppConfig):
    """Configuration class for wagtail-reusable-blocks."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "wagtail_reusable_blocks"
    verbose_name = "Wagtail Reusable Blocks"

    def ready(self) -> None:
        """
        Perform initialization when Django starts.

        Validates settings configuration.
        """
        from .conf import get_setting

        # Validate BLOCK_TYPES setting
        block_types = get_setting("BLOCK_TYPES")

        if not block_types:
            logger.warning(
                "WAGTAIL_REUSABLE_BLOCKS['BLOCK_TYPES'] is empty. "
                "Using default block types."
            )

        if not isinstance(block_types, list):
            raise ImproperlyConfigured(
                "WAGTAIL_REUSABLE_BLOCKS['BLOCK_TYPES'] must be a list of tuples. "
                f"Got {type(block_types).__name__} instead."
            )

        # Validate each block type is a tuple with 2 elements
        for i, block_type in enumerate(block_types):
            if not isinstance(block_type, tuple) or len(block_type) != 2:
                raise ImproperlyConfigured(
                    f"WAGTAIL_REUSABLE_BLOCKS['BLOCK_TYPES'][{i}] must be a "
                    f"tuple of (name, block_instance). Got {block_type!r}"
                )

            name, block = block_type
            if not isinstance(name, str):
                raise ImproperlyConfigured(
                    f"WAGTAIL_REUSABLE_BLOCKS['BLOCK_TYPES'][{i}] name must be a "
                    f"string. Got {type(name).__name__}"
                )

            # Check if block has required StreamField block methods
            if not hasattr(block, "render"):
                raise ImproperlyConfigured(
                    f"WAGTAIL_REUSABLE_BLOCKS['BLOCK_TYPES'][{i}] block instance "
                    f"'{name}' does not appear to be a valid Wagtail block "
                    "(missing 'render' method)."
                )

        # Validate TEMPLATE setting
        template = get_setting("TEMPLATE")
        if not isinstance(template, str):
            raise ImproperlyConfigured(
                "WAGTAIL_REUSABLE_BLOCKS['TEMPLATE'] must be a string. "
                f"Got {type(template).__name__} instead."
            )
