"""Template tags and filters for wagtail-reusable-blocks."""

import os
from typing import Any

from django import template

register = template.Library()


@register.filter
def is_gif(image: Any) -> bool:
    """Check if an image is a GIF file.

    Args:
        image: A Wagtail Image instance

    Returns:
        True if the image is a GIF file, False otherwise
    """
    if not image or not hasattr(image, "file") or not image.file:
        return False
    _, ext = os.path.splitext(image.file.name)
    return bool(ext.lower() == ".gif")


@register.filter
def is_svg(image: Any) -> bool:
    """Check if an image is an SVG file.

    Args:
        image: A Wagtail Image instance

    Returns:
        True if the image is an SVG file, False otherwise
    """
    if not image or not hasattr(image, "file") or not image.file:
        return False
    _, ext = os.path.splitext(image.file.name)
    return bool(ext.lower() == ".svg")
