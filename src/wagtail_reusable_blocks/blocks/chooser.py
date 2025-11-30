"""Chooser block for selecting ReusableBlock snippets."""

from typing import TYPE_CHECKING, Any

from django.utils.safestring import SafeString
from wagtail.snippets.blocks import SnippetChooserBlock

from ..models import ReusableBlock

if TYPE_CHECKING:
    from wagtail.snippets.blocks import SnippetChooserBlock as SnippetChooserBlockType
else:
    SnippetChooserBlockType = SnippetChooserBlock  # type: ignore[misc,assignment]


class ReusableBlockChooserBlock(SnippetChooserBlockType):  # type: ignore[misc]
    """Block for selecting and rendering a ReusableBlock snippet.

    This block integrates with Wagtail's chooser interface to allow editors
    to select a ReusableBlock from the admin. The selected block's content
    is rendered on the frontend using the block's template.

    Usage:
        In your page model's StreamField:

        >>> from wagtail.fields import StreamField
        >>> from wagtail_reusable_blocks.blocks import ReusableBlockChooserBlock
        >>>
        >>> class MyPage(Page):
        ...     body = StreamField([
        ...         ('reusable_block', ReusableBlockChooserBlock()),
        ...         # ... other blocks
        ...     ])

    Template rendering:
        The block automatically renders using ReusableBlock.render():

        >>> # In template
        >>> {% load wagtailcore_tags %}
        >>> {% for block in page.body %}
        ...     {% include_block block %}
        ... {% endfor %}

    Edge cases:
        - Deleted blocks: Renders empty string (no error)
        - Empty content: Renders empty string
        - None value: Renders empty string
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the chooser block for ReusableBlock model."""
        super().__init__(target_model=ReusableBlock, **kwargs)

    def render_basic(
        self, value: ReusableBlock | None, context: dict[str, Any] | None = None
    ) -> SafeString | str:
        """Render the selected ReusableBlock's content.

        Args:
            value: The selected ReusableBlock instance, or None
            context: Template context to pass to the block's render method

        Returns:
            Rendered HTML from the ReusableBlock's template, or empty string
            if value is None or deleted.

        Example:
            >>> block = ReusableBlockChooserBlock()
            >>> reusable_block = ReusableBlock.objects.get(slug='header')
            >>> html = block.render_basic(reusable_block)
            >>> # Returns rendered HTML from the block's template
        """
        if value is None:
            return ""

        try:
            # Pass the context to the block's render method
            return value.render(context=context)
        except Exception:
            # Handle deleted blocks or rendering errors gracefully
            # Return empty string instead of breaking the page
            return ""

    class Meta:
        icon = "snippet"
