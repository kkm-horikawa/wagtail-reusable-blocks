"""Configuration and settings for wagtail-reusable-blocks."""

from typing import Any

from django.conf import settings

# Default settings
DEFAULTS = {
    # v0.1.0 settings
    "TEMPLATE": "wagtail_reusable_blocks/reusable_block.html",
    "REGISTER_DEFAULT_SNIPPET": True,
    "MAX_NESTING_DEPTH": 5,
    # v0.2.0 settings
    "SLOT_ATTRIBUTE": "data-slot",
    "SLOT_LABEL_ATTRIBUTE": "data-slot-label",
    # v0.3.0 settings - Caching
    "CACHE_ENABLED": True,
    "CACHE_BACKEND": "default",
    "CACHE_TIMEOUT": 3600,  # 1 hour
    "CACHE_PREFIX": "wrb:",
    # v0.5.0 settings - Preview
    "PREVIEW_TEMPLATE": "wagtail_reusable_blocks/preview.html",
}


def get_setting(key: str, default: Any = None) -> Any:
    """
    Get a setting from Django settings or return default value.

    Args:
        key: The setting key to retrieve
        default: Default value if not found (overrides DEFAULTS)

    Returns:
        The setting value or default

    Example:
        >>> get_setting('TEMPLATE')
        'wagtail_reusable_blocks/reusable_block.html'
    """
    user_settings = getattr(settings, "WAGTAIL_REUSABLE_BLOCKS", {})

    # Use provided default, or fall back to DEFAULTS
    fallback = default if default is not None else DEFAULTS.get(key)

    return user_settings.get(key, fallback)
