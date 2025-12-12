"""ReusableBlock model for wagtail-reusable-blocks."""

from typing import TYPE_CHECKING, Any

from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models
from django.template.loader import render_to_string
from django.utils.safestring import SafeString, mark_safe
from django.utils.text import slugify
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, PublishingPanel
from wagtail.blocks import RawHTMLBlock, RichTextBlock, TextBlock
from wagtail.fields import StreamField
from wagtail.models import (
    DraftStateMixin,
    LockableMixin,
    PreviewableMixin,
    RevisionMixin,
    WorkflowMixin,
)
from wagtail.search import index
from wagtail.snippets.blocks import SnippetChooserBlock

if TYPE_CHECKING:
    from django.template.context import Context


# Use EnhancedHTMLBlock if wagtail-html-editor is installed, otherwise fallback
try:
    from wagtail_html_editor.blocks import (  # type: ignore[import-not-found]
        EnhancedHTMLBlock,
    )

    _HTMLBlock = EnhancedHTMLBlock  # pragma: no cover
except ImportError:
    _HTMLBlock = RawHTMLBlock


class _HeadInjectionBlock(TextBlock):  # type: ignore[misc]
    """Block for injecting CSS/JS into <head> during snippet preview only.

    This is an internal class used in the default ReusableBlock content.
    For external use, import HeadInjectionBlock from wagtail_reusable_blocks.blocks.

    The content is only applied during preview and ignored during normal rendering.
    """

    def render_basic(
        self, value: str | None, context: dict[str, Any] | None = None
    ) -> str:
        """Return empty string during normal rendering."""
        return ""

    class Meta:
        icon = "code"
        label = _("Preview Head Injection")


class _ReusableBlockChooserBlock(SnippetChooserBlock):  # type: ignore[misc]
    """Internal SnippetChooserBlock that renders ReusableBlock content.

    This is an internal class used in the default ReusableBlock content.
    Standard SnippetChooserBlock.render_basic returns str(value) (the name),
    but we need to render the actual content of the nested block.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with ReusableBlock as the target model."""
        super().__init__(target_model="wagtail_reusable_blocks.ReusableBlock", **kwargs)

    def render_basic(
        self, value: Any, context: dict[str, Any] | None = None
    ) -> SafeString | str:
        """Render the selected ReusableBlock's content instead of its name.

        Args:
            value: The selected ReusableBlock instance or None.
            context: Optional context dictionary for rendering.

        Returns:
            Rendered HTML content of the ReusableBlock.
        """
        if value is None:
            return ""

        if context is None:
            context = {}

        # Import here to avoid circular imports
        from ..conf import get_setting

        # Track nesting depth to prevent infinite recursion
        current_depth = context.get("_reusable_block_depth", 0)
        max_depth = get_setting("MAX_NESTING_DEPTH")

        if current_depth >= max_depth:
            return mark_safe(
                '<div class="reusable-block-max-depth-warning">'
                + str(_("Maximum nesting depth exceeded"))
                + "</div>"
            )

        try:
            # Create new context with incremented depth
            nested_context = context.copy()
            nested_context["_reusable_block_depth"] = current_depth + 1

            # Render the nested block's content
            rendered: SafeString | str = value.render(context=nested_context)
            return rendered
        except Exception:
            return ""

    class Meta:
        icon = "snippet"
        label = _("Reusable Block")


class ReusableBlock(
    WorkflowMixin,  # type: ignore[misc]
    DraftStateMixin,  # type: ignore[misc]
    LockableMixin,  # type: ignore[misc]
    RevisionMixin,  # type: ignore[misc]
    PreviewableMixin,  # type: ignore[misc]
    index.Indexed,  # type: ignore[misc]
    models.Model,
):
    """Reusable content blocks that can be used across multiple pages.

    By default, this model is automatically registered as a Wagtail Snippet
    and ready to use immediately after installation. The default includes
    RichTextBlock, RawHTMLBlock, nested ReusableBlock support, and HeadInjectionBlock
    for preview-only CSS/JS injection.

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
        content: StreamField containing the block content (RichTextBlock, RawHTMLBlock,
                 ReusableBlock, and HeadInjectionBlock by default).
        created_at: Timestamp when the block was created.
        updated_at: Timestamp when the block was last updated.
    """

    # Constants
    MAX_NAME_LENGTH = 255

    # Fields
    name = models.CharField(
        _("name"),
        max_length=MAX_NAME_LENGTH,
        help_text=_("Human-readable name for this reusable block"),
    )
    slug = models.SlugField(
        _("slug"),
        unique=True,
        max_length=MAX_NAME_LENGTH,
        blank=True,
        help_text=_("URL-safe identifier, auto-generated from name"),
    )
    content = StreamField(
        [
            ("rich_text", RichTextBlock()),
            ("raw_html", _HTMLBlock()),
            ("reusable_block", _ReusableBlockChooserBlock()),
            ("head_injection", _HeadInjectionBlock()),
        ],
        use_json_field=True,
        blank=True,
        verbose_name=_("content"),
        help_text=_("The content of this reusable block"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # GenericRelation for revisions (required for RevisionMixin)
    _revisions = GenericRelation(
        "wagtailcore.Revision",
        related_query_name="reusableblock",
    )

    # GenericRelation for workflow states (required for WorkflowMixin)
    workflow_states = GenericRelation(
        "wagtailcore.WorkflowState",
        content_type_field="base_content_type",
        object_id_field="object_id",
        related_query_name="reusableblock",
        for_concrete_model=False,
    )

    # Admin panels
    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("content"),
        PublishingPanel(),
    ]

    # Search configuration
    search_fields = [
        index.SearchField("name", partial_match=True),
        index.SearchField("slug", partial_match=True),
        index.AutocompleteField("name"),
    ]

    class Meta:
        """Model metadata."""

        ordering = ["-updated_at"]
        verbose_name = _("Reusable Block")
        verbose_name_plural = _("Reusable Blocks")
        indexes = [
            models.Index(fields=["slug"]),
        ]

    def __str__(self) -> str:
        """Return string representation of the block."""
        return self.name

    def save(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        """Save the model, auto-generating slug if not provided.

        Raises:
            ValidationError: If circular reference is detected.
        """
        if not self.slug:
            self.slug = slugify(self.name)

        # Validate for circular references before saving
        self.clean()

        super().save(*args, **kwargs)

    def clean(self) -> None:
        """Validate the model for circular references.

        Raises:
            ValidationError: If circular reference is detected.
        """
        try:
            self._detect_circular_references()
        except ValidationError:
            raise

    def _detect_circular_references(self, visited: set[int] | None = None) -> None:
        """Detect circular references in nested ReusableBlocks.

        Args:
            visited: Set of visited block IDs to track the traversal path.

        Raises:
            ValidationError: If a circular reference is detected.
        """
        # Skip validation if block hasn't been saved yet (no ID)
        if not self.pk:
            return

        # Initialize visited set for root call
        if visited is None:
            visited = set()

        # Check for self-reference
        if self.pk in visited:
            raise ValidationError(
                gettext(
                    "Circular reference detected: Block '%(name)s' (id=%(id)s) "
                    "references itself in the dependency chain."
                )
                % {"name": self.name, "id": self.pk}
            )

        # Add current block to visited set
        visited.add(self.pk)

        # Get all referenced ReusableBlocks from content
        referenced_blocks = self._get_referenced_blocks()

        # Recursively check each referenced block
        for block in referenced_blocks:
            try:
                block._detect_circular_references(visited.copy())
            except ValidationError as e:
                # Re-raise with additional context
                raise ValidationError(
                    gettext(
                        "Circular reference detected: Block '%(name)s' references "
                        "block '%(ref_name)s' which creates a cycle. %(error)s"
                    )
                    % {"name": self.name, "ref_name": block.name, "error": str(e)}
                ) from e

    def _get_referenced_blocks(self) -> list["ReusableBlock"]:
        """Extract all ReusableBlock references from the content StreamField.

        Extended in v0.2.0 to also check ReusableLayoutBlock slot content.

        Returns:
            List of ReusableBlock instances referenced in the content.
        """
        from ..blocks import ReusableLayoutBlock

        referenced_blocks: list[ReusableBlock] = []

        # Iterate through all blocks in the content StreamField
        for block in self.content:
            # Check SnippetChooserBlock (includes ReusableBlockChooserBlock subclass)
            if isinstance(block.block, SnippetChooserBlock):
                if block.value and isinstance(block.value, ReusableBlock):
                    referenced_blocks.append(block.value)

            # v0.2.0: Check ReusableLayoutBlock
            elif isinstance(block.block, ReusableLayoutBlock):
                layout_value = block.value

                # Add the layout itself
                if layout_value and "layout" in layout_value:
                    layout_block = layout_value["layout"]
                    if isinstance(layout_block, ReusableBlock):
                        referenced_blocks.append(layout_block)

                # Check slot content for nested blocks
                if layout_value and "slot_content" in layout_value:
                    for slot_fill in layout_value["slot_content"]:
                        slot_fill_value = slot_fill.value
                        if "content" in slot_fill_value:
                            # Recursively check slot content
                            nested = self._get_blocks_from_streamfield(
                                slot_fill_value["content"]
                            )
                            referenced_blocks.extend(nested)

        return referenced_blocks

    def _get_blocks_from_streamfield(
        self, streamfield_value: Any
    ) -> list["ReusableBlock"]:
        """Extract ReusableBlocks from a StreamField value.

        Helper method to recursively find blocks in nested StreamFields.

        Args:
            streamfield_value: List of BoundBlock instances

        Returns:
            List of referenced ReusableBlocks
        """
        from ..blocks import ReusableLayoutBlock

        blocks: list[ReusableBlock] = []

        for bound_block in streamfield_value:
            block_type = bound_block.block

            # Check SnippetChooserBlock (includes ReusableBlockChooserBlock subclass)
            if isinstance(block_type, SnippetChooserBlock):
                if bound_block.value and isinstance(bound_block.value, ReusableBlock):
                    blocks.append(bound_block.value)

            # ReusableLayoutBlock (recursive)
            elif isinstance(block_type, ReusableLayoutBlock):
                layout_value = bound_block.value

                # Add layout
                if "layout" in layout_value:
                    layout_block = layout_value["layout"]
                    if isinstance(layout_block, ReusableBlock):
                        blocks.append(layout_block)

                # Check slot content
                if "slot_content" in layout_value:
                    for slot_fill in layout_value["slot_content"]:
                        if "content" in slot_fill.value:
                            nested = self._get_blocks_from_streamfield(
                                slot_fill.value["content"]
                            )
                            blocks.extend(nested)

        return blocks

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

    @property
    def revisions(self) -> GenericRelation:
        """Return the revisions relation for RevisionMixin compatibility."""
        return self._revisions  # type: ignore[no-any-return]

    def get_preview_template(self, request: Any = None, mode_name: str = "") -> str:
        """Return the template to use for previewing this block.

        Required by PreviewableMixin. Uses a standalone preview template
        that includes a full HTML document with <head> support for
        HeadInjectionBlock content.

        Args:
            request: The HTTP request object.
            mode_name: The preview mode name.

        Returns:
            Template path for rendering preview.
        """
        from ..conf import get_setting

        return str(get_setting("PREVIEW_TEMPLATE"))

    def get_preview_context(
        self, request: Any = None, mode_name: str = ""
    ) -> dict[str, Any]:
        """Return context for previewing this block.

        Required by PreviewableMixin. Collects HeadInjectionBlock content
        to be injected into the preview template's <head> tag.

        Args:
            request: The HTTP request object.
            mode_name: The preview mode name.

        Returns:
            Context dictionary for template rendering.
        """
        # Collect HeadInjectionBlock content
        head_injection_content = []
        for block in self.content:
            if block.block_type == "head_injection" and block.value:
                head_injection_content.append(block.value)

        return {
            "block": self,
            "head_injection_content": head_injection_content,
        }
