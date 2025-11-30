"""Tests for circular reference detection and nesting depth."""

import pytest
from django.core.exceptions import ValidationError

from wagtail_reusable_blocks.models import ReusableBlock


@pytest.mark.django_db
class TestCircularReferenceDetection:
    """Tests for circular reference detection logic."""

    def test_get_referenced_blocks_empty_content(self):
        """_get_referenced_blocks returns empty list for block with no refs."""
        block = ReusableBlock.objects.create(
            name="Simple Block", content=[("rich_text", "<p>Content</p>")]
        )

        referenced = block._get_referenced_blocks()
        assert referenced == []

    def test_detect_circular_references_no_refs(self):
        """Block with no references passes validation."""
        block = ReusableBlock.objects.create(
            name="Simple Block", content=[("rich_text", "<p>Content</p>")]
        )

        # Should not raise any error
        block._detect_circular_references()

    def test_detect_circular_references_visited_tracking(self):
        """Visited set tracks blocks in the dependency chain."""
        block = ReusableBlock.objects.create(
            name="Test Block", content=[("rich_text", "<p>Content</p>")]
        )

        # Simulate being in a visited chain
        visited = {block.pk}

        # Should detect self-reference
        with pytest.raises(ValidationError, match="Circular reference detected"):
            block._detect_circular_references(visited=visited)

    def test_clean_method_calls_circular_detection(self):
        """clean() method calls _detect_circular_references."""
        block = ReusableBlock.objects.create(
            name="Test Block", content=[("rich_text", "<p>Content</p>")]
        )

        # Should not raise (no circular ref)
        block.clean()

    def test_save_calls_clean(self):
        """save() method calls clean() for validation."""
        block = ReusableBlock(
            name="Test Block", content=[("rich_text", "<p>Content</p>")]
        )

        # Should save successfully (no circular ref)
        block.save()
        assert block.pk is not None


@pytest.mark.django_db
class TestNestingDepthConfiguration:
    """Tests for MAX_NESTING_DEPTH configuration."""

    def test_default_max_nesting_depth(self):
        """Default MAX_NESTING_DEPTH is 5."""
        from wagtail_reusable_blocks.conf import get_setting

        max_depth = get_setting("MAX_NESTING_DEPTH")
        assert max_depth == 5

    def test_custom_max_nesting_depth(self, settings):
        """Custom MAX_NESTING_DEPTH can be configured."""
        settings.WAGTAIL_REUSABLE_BLOCKS = {"MAX_NESTING_DEPTH": 10}

        from wagtail_reusable_blocks.conf import get_setting

        max_depth = get_setting("MAX_NESTING_DEPTH")
        assert max_depth == 10


@pytest.mark.django_db
class TestRenderBasicDepthTracking:
    """Tests for depth tracking in ReusableBlockChooserBlock.render_basic()."""

    def test_depth_tracking_in_context(self):
        """Depth is tracked in context during rendering."""
        from wagtail_reusable_blocks.blocks import ReusableBlockChooserBlock

        block_chooser = ReusableBlockChooserBlock()
        reusable_block = ReusableBlock.objects.create(
            name="Test Block", content=[("rich_text", "<p>Content</p>")]
        )

        # Initial render (depth 0)
        context = {}
        html = block_chooser.render_basic(reusable_block, context=context)

        # Should render content
        assert "<p>Content</p>" in html

    def test_max_depth_exceeded_warning(self):
        """Warning shown when max depth is exceeded."""
        from wagtail_reusable_blocks.blocks import ReusableBlockChooserBlock

        block_chooser = ReusableBlockChooserBlock()
        reusable_block = ReusableBlock.objects.create(
            name="Deep Block", content=[("rich_text", "<p>Content</p>")]
        )

        # Simulate being at max depth already
        context = {"_reusable_block_depth": 5}  # Max is 5, so this is at limit
        html = block_chooser.render_basic(reusable_block, context=context)

        # Should show warning instead of content
        assert "Maximum nesting depth exceeded" in html
        assert "<p>Content</p>" not in html

    def test_depth_increments_correctly(self):
        """Depth increments with each level of nesting."""
        from wagtail_reusable_blocks.blocks import ReusableBlockChooserBlock

        block_chooser = ReusableBlockChooserBlock()
        reusable_block = ReusableBlock.objects.create(
            name="Test Block", content=[("rich_text", "<p>Content</p>")]
        )

        # Start at depth 0
        context = {"_reusable_block_depth": 0}
        html = block_chooser.render_basic(reusable_block, context=context)

        # Content should render (not at max depth yet)
        assert "<p>Content</p>" in html

        # Try at depth 4 (one below max of 5)
        context = {"_reusable_block_depth": 4}
        html = block_chooser.render_basic(reusable_block, context=context)

        # Still should render
        assert "<p>Content</p>" in html

    def test_none_context_initializes_depth(self):
        """None context is initialized with depth 0."""
        from wagtail_reusable_blocks.blocks import ReusableBlockChooserBlock

        block_chooser = ReusableBlockChooserBlock()
        reusable_block = ReusableBlock.objects.create(
            name="Test Block", content=[("rich_text", "<p>Content</p>")]
        )

        # Pass None as context
        html = block_chooser.render_basic(reusable_block, context=None)

        # Should render normally
        assert "<p>Content</p>" in html

    def test_depth_warning_logged(self, caplog):
        """Warning is logged when max depth is exceeded."""
        import logging

        from wagtail_reusable_blocks.blocks import ReusableBlockChooserBlock

        caplog.set_level(logging.WARNING)

        block_chooser = ReusableBlockChooserBlock()
        reusable_block = ReusableBlock.objects.create(
            name="Deep Block", content=[("rich_text", "<p>Content</p>")]
        )

        # Exceed max depth
        context = {"_reusable_block_depth": 10}
        block_chooser.render_basic(reusable_block, context=context)

        # Check that warning was logged
        assert any(
            "Maximum nesting depth" in record.message for record in caplog.records
        )
