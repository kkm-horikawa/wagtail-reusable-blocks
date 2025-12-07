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
class TestCircularReferenceWithNesting:
    """Tests for circular reference detection with actual nested blocks.

    Note: Since v0.5.0, ReusableBlockChooserBlock is included in the default
    content StreamField, so no patching is required.
    """

    def test_actual_circular_reference_detected(self):
        """Detect circular reference: A → B → A."""
        # Create block A
        block_a = ReusableBlock.objects.create(
            name="Block A", content=[("rich_text", "<p>A</p>")]
        )

        # Create block B
        block_b = ReusableBlock.objects.create(
            name="Block B", content=[("rich_text", "<p>B</p>")]
        )

        # Make A reference B
        block_a.content = [("reusable_block", block_b)]
        block_a.save()

        # Make B reference A (creates cycle)
        block_b.content = [("reusable_block", block_a)]

        # Should raise ValidationError
        with pytest.raises(ValidationError, match="Circular reference detected"):
            block_b.save()

    def test_actual_self_reference_detected(self):
        """Detect self-reference: A → A."""
        # Create block A
        block_a = ReusableBlock.objects.create(
            name="Block A", content=[("rich_text", "<p>A</p>")]
        )

        # Make A reference itself
        block_a.content = [("reusable_block", block_a)]

        # Should raise ValidationError
        with pytest.raises(ValidationError, match="Circular reference detected"):
            block_a.save()

    def test_actual_three_way_cycle_detected(self):
        """Detect three-way cycle: A → B → C → A."""
        # Create blocks
        block_a = ReusableBlock.objects.create(
            name="Block A", content=[("rich_text", "<p>A</p>")]
        )
        block_b = ReusableBlock.objects.create(
            name="Block B", content=[("rich_text", "<p>B</p>")]
        )
        block_c = ReusableBlock.objects.create(
            name="Block C", content=[("rich_text", "<p>C</p>")]
        )

        # A → B
        block_a.content = [("reusable_block", block_b)]
        block_a.save()

        # B → C
        block_b.content = [("reusable_block", block_c)]
        block_b.save()

        # C → A (creates cycle)
        block_c.content = [("reusable_block", block_a)]

        # Should raise ValidationError
        with pytest.raises(ValidationError, match="Circular reference detected"):
            block_c.save()

    def test_linear_chain_allowed(self):
        """Linear chain without cycle should work: A → B → C."""
        # Create blocks
        block_a = ReusableBlock.objects.create(
            name="Block A", content=[("rich_text", "<p>A</p>")]
        )
        block_b = ReusableBlock.objects.create(
            name="Block B", content=[("rich_text", "<p>B</p>")]
        )
        block_c = ReusableBlock.objects.create(
            name="Block C", content=[("rich_text", "<p>C</p>")]
        )

        # A → B
        block_a.content = [("reusable_block", block_b)]
        block_a.save()

        # B → C
        block_b.content = [("reusable_block", block_c)]
        block_b.save()

        # Should succeed (no cycle)
        assert block_a.pk is not None
        assert block_b.pk is not None

    def test_get_referenced_blocks_finds_nested(self):
        """_get_referenced_blocks finds nested ReusableBlockChooserBlock."""
        # Create blocks
        block_a = ReusableBlock.objects.create(
            name="Block A", content=[("rich_text", "<p>A</p>")]
        )
        block_b = ReusableBlock.objects.create(
            name="Block B", content=[("rich_text", "<p>B</p>")]
        )

        # A → B
        block_a.content = [("reusable_block", block_b)]
        block_a.save()

        # Get referenced blocks
        referenced = block_a._get_referenced_blocks()

        # Should find block_b
        assert len(referenced) == 1
        assert referenced[0].pk == block_b.pk

    def test_multiple_references_found(self):
        """_get_referenced_blocks finds multiple nested blocks."""
        # Create blocks
        block_a = ReusableBlock.objects.create(
            name="Block A", content=[("rich_text", "<p>A</p>")]
        )
        block_b = ReusableBlock.objects.create(
            name="Block B", content=[("rich_text", "<p>B</p>")]
        )
        block_c = ReusableBlock.objects.create(
            name="Block C", content=[("rich_text", "<p>C</p>")]
        )

        # A → B and C
        block_a.content = [
            ("reusable_block", block_b),
            ("rich_text", "<p>Middle</p>"),
            ("reusable_block", block_c),
        ]
        block_a.save()

        # Get referenced blocks
        referenced = block_a._get_referenced_blocks()

        # Should find both blocks
        assert len(referenced) == 2
        referenced_pks = {b.pk for b in referenced}
        assert block_b.pk in referenced_pks
        assert block_c.pk in referenced_pks


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
