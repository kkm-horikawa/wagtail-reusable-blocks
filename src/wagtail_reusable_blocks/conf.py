"""Configuration and settings for wagtail-reusable-blocks."""

from typing import Any

from django.conf import settings
from wagtail.blocks import RawHTMLBlock, RichTextBlock

# Default settings
DEFAULTS = {
    "BLOCK_TYPES": [
        ("rich_text", RichTextBlock()),
        ("raw_html", RawHTMLBlock()),
    ],
    "TEMPLATE": "wagtail_reusable_blocks/reusable_block.html",
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
        >>> get_setting('BLOCK_TYPES')
        [('rich_text', RichTextBlock()), ('raw_html', RawHTMLBlock())]
    """
    user_settings = getattr(settings, "WAGTAIL_REUSABLE_BLOCKS", {})

    # Use provided default, or fall back to DEFAULTS
    fallback = default if default is not None else DEFAULTS.get(key)

    return user_settings.get(key, fallback)
