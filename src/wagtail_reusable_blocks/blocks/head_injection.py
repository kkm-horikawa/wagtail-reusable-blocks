"""HeadInjectionBlock for preview-only CSS/JS injection."""

from typing import Any

from django.utils.translation import gettext_lazy as _
from wagtail.blocks import TextBlock


class HeadInjectionBlock(TextBlock):  # type: ignore[misc]
    """Block for injecting CSS/JS into <head> during snippet preview only.

    This block allows users to include CSS frameworks (like Bootstrap, Tailwind)
    or custom styles that will only be applied during the snippet preview.
    The content is ignored during normal page rendering.

    Usage:
        Add to a custom ReusableBlock subclass or page StreamField:

        ```python
        from wagtail_reusable_blocks.blocks import HeadInjectionBlock

        content = StreamField([
            ("head_injection", HeadInjectionBlock()),
            ("rich_text", RichTextBlock()),
        ])
        ```

        Then in the block content:

        ```html
        <!-- Bootstrap CDN -->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

        <!-- Custom preview styles -->
        <style>
          .my-component { padding: 20px; }
        </style>
        ```

    Note:
        The default ReusableBlock model already includes HeadInjectionBlock.
        This class is exported for use in custom models.

    Security Note:
        - Only admin users can edit this block
        - Content is only loaded during preview, not in production
        - Be cautious with external scripts from untrusted sources
    """

    def render_basic(
        self, value: str | None, context: dict[str, Any] | None = None
    ) -> str:
        """Return empty string during normal rendering.

        HeadInjectionBlock content is only used in the preview template,
        not during normal page rendering.

        Args:
            value: The block content
            context: Template context

        Returns:
            Empty string (content is handled by preview template)
        """
        return ""

    class Meta:
        icon = "code"
        label = _("Preview Head Injection")
