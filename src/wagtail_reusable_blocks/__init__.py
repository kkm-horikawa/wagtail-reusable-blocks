"""Reusable content blocks with slot-based templating for Wagtail CMS."""

default_app_config = "wagtail_reusable_blocks.apps.WagtailReusableBlocksConfig"


def __getattr__(name: str):  # type: ignore[no-untyped-def]
    """Lazy import to avoid circular dependencies."""
    if name == "ReusableBlock":
        from .models import ReusableBlock

        return ReusableBlock
    if name == "ReusableBlockChooserBlock":
        from .blocks import ReusableBlockChooserBlock

        return ReusableBlockChooserBlock
    if name == "ImageBlock":
        from .blocks import ImageBlock

        return ImageBlock
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["ImageBlock", "ReusableBlock", "ReusableBlockChooserBlock"]
