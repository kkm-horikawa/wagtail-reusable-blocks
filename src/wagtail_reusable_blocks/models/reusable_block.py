"""ReusableBlock model for wagtail-reusable-blocks."""

from django.db import models
from django.utils.text import slugify
from wagtail.admin.panels import FieldPanel
from wagtail.blocks import RawHTMLBlock, RichTextBlock
from wagtail.fields import StreamField


class ReusableBlock(models.Model):
    """Reusable content blocks that can be used across multiple pages.

    By default, this model is automatically registered as a Wagtail Snippet
    and ready to use immediately after installation. The default includes
    RichTextBlock and RawHTMLBlock.

    Quick Start (No Code Required):
        1. Add 'wagtail_reusable_blocks' to INSTALLED_APPS
        2. Run migrations: python manage.py migrate
        3. Access "Reusable Blocks" in Wagtail admin

    Adding Custom Block Types:
        To add more block types (e.g., images, videos), create your own model:

        from wagtail.blocks import CharBlock, ImageChooserBlock, RichTextBlock, RawHTMLBlock
        from wagtail.fields import StreamField
        from wagtail.snippets.models import register_snippet
        from wagtail_reusable_blocks.models import ReusableBlock

        @register_snippet
        class CustomReusableBlock(ReusableBlock):
            # Override content field with additional block types
            content = StreamField([
                ('rich_text', RichTextBlock()),      # Keep defaults
                ('raw_html', RawHTMLBlock()),        # Keep defaults
                ('image', ImageChooserBlock()),      # Add image support
                ('heading', CharBlock()),            # Add heading support
            ], use_json_field=True, blank=True)

            class Meta(ReusableBlock.Meta):
                verbose_name = "Reusable Block"
                verbose_name_plural = "Reusable Blocks"

        # Disable the default snippet to avoid duplicates
        WAGTAIL_REUSABLE_BLOCKS = {
            'REGISTER_DEFAULT_SNIPPET': False,
        }

    Completely Custom Block:
        For specialized use cases, create a completely different block:

        @register_snippet
        class HeaderBlock(ReusableBlock):
            content = StreamField([
                ('heading', CharBlock()),
                ('subheading', CharBlock(required=False)),
            ], use_json_field=True, blank=True)

            class Meta(ReusableBlock.Meta):
                verbose_name = "Header Block"

    Attributes:
        name: Human-readable identifier for the block.
        slug: URL-safe unique identifier, auto-generated from name.
        content: StreamField containing the block content (RichTextBlock and RawHTMLBlock by default).
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
