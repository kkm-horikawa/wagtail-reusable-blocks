"""Tests for custom widgets."""

from wagtail_reusable_blocks.blocks import ReusableLayoutBlock
from wagtail_reusable_blocks.widgets import ReusableLayoutBlockAdapter


class TestReusableLayoutBlockAdapter:
    """Tests for ReusableLayoutBlockAdapter."""

    def test_adapter_includes_javascript(self):
        """Adapter includes slot-chooser.js with auto-initialization."""
        adapter = ReusableLayoutBlockAdapter()

        media = adapter.media
        js_files = [str(js) for js in media._js]

        # Should include slot-chooser.js (auto-initializes on DOM ready)
        assert any("slot-chooser.js" in js for js in js_files)


class TestReusableLayoutBlockIntegration:
    """Tests for ReusableLayoutBlock integration with adapter."""

    def test_block_uses_custom_adapter(self):
        """ReusableLayoutBlock uses ReusableLayoutBlockAdapter."""
        block = ReusableLayoutBlock()

        # Check that the block's Meta has adapter_class set
        assert hasattr(block.meta, "adapter_class")
        assert block.meta.adapter_class == ReusableLayoutBlockAdapter
