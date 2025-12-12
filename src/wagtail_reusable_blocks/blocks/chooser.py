"""Chooser block for selecting ReusableBlock snippets."""

from typing import TYPE_CHECKING, Any

from django.utils.safestring import SafeString
from django.utils.translation import gettext_lazy as _
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

        Implements depth tracking to prevent infinite recursion from nested blocks.
        If maximum nesting depth is exceeded, shows a warning message instead.

        Caching:
            Results are cached using ReusableBlockCache when enabled.
            Cache is skipped for nested blocks to ensure context propagation.

        Args:
            value: The selected ReusableBlock instance, or None
            context: Template context to pass to the block's render method

        Returns:
            Rendered HTML from the ReusableBlock's template, or empty string
            if value is None or deleted. Returns warning message if max depth exceeded.

        Example:
            >>> block = ReusableBlockChooserBlock()
            >>> reusable_block = ReusableBlock.objects.get(slug='header')
            >>> html = block.render_basic(reusable_block)
            >>> # Returns rendered HTML from the block's template
        """
        if value is None:
            return ""

        # Initialize context if None
        if context is None:
            context = {}

        # Track nesting depth to prevent infinite recursion
        current_depth = context.get("_reusable_block_depth", 0)

        # Get max depth from settings
        from ..conf import get_setting

        max_depth = get_setting("MAX_NESTING_DEPTH")

        # Check if we've exceeded maximum nesting depth
        if current_depth >= max_depth:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"Maximum nesting depth ({max_depth}) exceeded for "
                f"ReusableBlock '{value.name}' (id={value.pk})"
            )
            return (
                '<div class="reusable-block-max-depth-warning">'
                + str(_("Maximum nesting depth exceeded"))
                + "</div>"
            )

        try:
            # Only use cache for top-level blocks (depth=0) to avoid
            # caching context-dependent nested content
            use_cache = current_depth == 0

            if use_cache:
                from ..cache import ReusableBlockCache

                cached = ReusableBlockCache.get(value.pk)
                if cached is not None:
                    return cached

            # Increment depth for nested rendering
            nested_context = context.copy()
            nested_context["_reusable_block_depth"] = current_depth + 1

            # Pass the context to the block's render method
            rendered = value.render(context=nested_context)

            # Cache the result for top-level blocks
            if use_cache:
                from ..cache import ReusableBlockCache

                ReusableBlockCache.set(value.pk, rendered)

            return rendered
        except Exception:
            # Handle deleted blocks or rendering errors gracefully
            # Return empty string instead of breaking the page
            return ""

    class Meta:
        icon = "snippet"
