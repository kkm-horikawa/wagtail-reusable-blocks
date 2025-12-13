"""
HTML block with optional enhanced editor support.

When wagtail-html-editor is installed, uses EnhancedHTMLBlock with
syntax highlighting, Emmet support, and fullscreen mode.
Otherwise, falls back to Wagtail's standard RawHTMLBlock.
"""

from wagtail.blocks import RawHTMLBlock

try:
    from wagtail_html_editor.blocks import (  # type: ignore[import-not-found]
        EnhancedHTMLBlock,
    )

    HTMLBlock = EnhancedHTMLBlock  # pragma: no cover
except ImportError:
    HTMLBlock = RawHTMLBlock

__all__ = ["HTMLBlock"]
