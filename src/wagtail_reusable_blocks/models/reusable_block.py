"""ReusableBlock model for wagtail-reusable-blocks."""

from django.db import models
from django.utils.text import slugify
from wagtail.admin.panels import FieldPanel
from wagtail.blocks import RawHTMLBlock, RichTextBlock
from wagtail.fields import StreamField


class ReusableBlock(models.Model):
    """Base model for reusable content blocks that can be used across multiple pages.

    This is an abstract-like base model that should be inherited and registered
    as a Wagtail Snippet in your project. It provides basic fields and functionality,
    with default RichTextBlock and RawHTMLBlock content types.

    Basic Usage:
        from wagtail.snippets.models import register_snippet
        from wagtail_reusable_blocks.models import ReusableBlock

        @register_snippet
        class MyReusableBlock(ReusableBlock):
            class Meta(ReusableBlock.Meta):
                verbose_name = "My Reusable Block"

    Custom Block Types:
        from wagtail.blocks import CharBlock, ImageChooserBlock
        from wagtail.fields import StreamField
        from wagtail.snippets.models import register_snippet
        from wagtail_reusable_blocks.models import ReusableBlock

        @register_snippet
        class CustomReusableBlock(ReusableBlock):
            content = StreamField([
                ('heading', CharBlock()),
                ('paragraph', RichTextBlock()),
                ('image', ImageChooserBlock()),
            ], use_json_field=True, blank=True)

            class Meta(ReusableBlock.Meta):
                verbose_name = "Custom Reusable Block"

    Attributes:
        name: Human-readable identifier for the block.
        slug: URL-safe unique identifier, auto-generated from name.
        content: StreamField containing the block content.
        created_at: Timestamp when the block was created.
        updated_at: Timestamp when the block was last updated.
    """

    # Constants
    MAX_NAME_LENGTH = 255

    # Fields
    name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        help_text="Human-readable name for this reusable block",
    )
    slug = models.SlugField(
        unique=True,
        max_length=MAX_NAME_LENGTH,
        help_text="URL-safe identifier, auto-generated from name",
    )
    content = StreamField(
        [
            ("rich_text", RichTextBlock()),
            ("raw_html", RawHTMLBlock()),
        ],
        use_json_field=True,
        blank=True,
        help_text="The content of this reusable block",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Admin panels
    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("content"),
    ]

    class Meta:
        """Model metadata."""

        ordering = ["-updated_at"]
        verbose_name = "Reusable Block"
        verbose_name_plural = "Reusable Blocks"
        indexes = [
            models.Index(fields=["slug"]),
        ]

    def __str__(self) -> str:
        """Return string representation of the block."""
        return self.name

    def save(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        """Save the model, auto-generating slug if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
