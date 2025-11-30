"""ReusableBlock model for wagtail-reusable-blocks."""

from typing import TYPE_CHECKING, Any

from django.db import models
from django.template.loader import render_to_string
from django.utils.safestring import SafeString, mark_safe
from django.utils.text import slugify
from wagtail.admin.panels import FieldPanel
from wagtail.blocks import RawHTMLBlock, RichTextBlock
from wagtail.fields import StreamField

if TYPE_CHECKING:
    from django.template.context import Context


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

    def render(
        self,
        context: "dict[str, Any] | Context | None" = None,
        template: str | None = None,
    ) -> SafeString:
        """Render the reusable block using a template.

        Args:
            context: Additional context to pass to the template.
                     Can be a dict or Django Context object.
                     Parent context is automatically included.
            template: Template path override. If not provided, uses the
                     TEMPLATE setting from WAGTAIL_REUSABLE_BLOCKS.

        Returns:
            Rendered HTML as a SafeString.

        Raises:
            TemplateDoesNotExist: If the specified template cannot be found.
                                  Check TEMPLATES['DIRS'] in settings.

        Example:
            >>> block = ReusableBlock.objects.get(slug='my-block')
            >>> html = block.render()
            >>> # With custom context (dict)
            >>> html = block.render(context={'page': page_object})
            >>> # With Django Context
            >>> from django.template import Context
            >>> html = block.render(context=Context({'page': page_object}))
            >>> # With custom template
            >>> html = block.render(template='custom/template.html')
        """
        from django.template import TemplateDoesNotExist

        from ..conf import get_setting

        template_name = template or get_setting("TEMPLATE")

        # Convert context to dict if needed (handles both dict and Context)
        render_context: dict[str, Any] = dict(context) if context else {}
        render_context["block"] = self

        try:
            return mark_safe(render_to_string(template_name, render_context))
        except TemplateDoesNotExist as e:
            # Provide helpful error message
            if template:
                msg = (
                    f"Template '{template_name}' not found. "
                    f"Make sure it exists in one of your TEMPLATES['DIRS'] "
                    f"or app template directories."
                )
            else:
                msg = (
                    f"Default template '{template_name}' not found. "
                    f"This may indicate a package installation issue. "
                    f"Try reinstalling wagtail-reusable-blocks or set a custom "
                    f"template via WAGTAIL_REUSABLE_BLOCKS['TEMPLATE']."
                )
            raise TemplateDoesNotExist(msg) from e
