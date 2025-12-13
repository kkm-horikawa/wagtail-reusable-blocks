"""Template tags and filters for wagtail-reusable-blocks."""

import os

from django import template

register = template.Library()


@register.filter
def is_gif(image):
    """Check if an image is a GIF file.

    Args:
        image: A Wagtail Image instance

    Returns:
        True if the image is a GIF file, False otherwise
    """
    if not image or not hasattr(image, "file") or not image.file:
        return False
    _, ext = os.path.splitext(image.file.name)
    return ext.lower() == ".gif"
