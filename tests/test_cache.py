"""Tests for ReusableBlockCache (Issue #67)."""

from django.core.cache import caches
from django.test import TestCase, override_settings

from wagtail_reusable_blocks.cache import ReusableBlockCache
from wagtail_reusable_blocks.models import ReusableBlock


class TestReusableBlockCacheSettings:
    """Tests for cache configuration."""

    def test_is_enabled_default(self):
        """Cache is disabled by default in tests."""
        # tests/settings.py sets CACHE_ENABLED = False
        assert ReusableBlockCache.is_enabled() is False

    def test_get_prefix_default(self):
        """Default cache prefix is 'wrb:'."""
        assert ReusableBlockCache.get_prefix() == "wrb:"

    def test_get_timeout_default(self):
        """Default cache timeout is 3600 seconds."""
        assert ReusableBlockCache.get_timeout() == 3600


class TestReusableBlockCacheKeyGeneration:
    """Tests for cache key generation."""

    def test_cache_key_simple(self):
        """Simple cache key for block without slot content."""
        key = ReusableBlockCache.get_cache_key(123)
        assert key == "wrb:123"

    def test_cache_key_with_slot_content(self):
        """Cache key includes hash when slot content is provided."""
        slot_content = [{"slot_id": "main", "content_repr": "test"}]
        key = ReusableBlockCache.get_cache_key(123, slot_content)
        assert key.startswith("wrb:123:")
        assert len(key) > len("wrb:123:")

    def test_cache_key_different_slot_content(self):
        """Different slot content produces different cache keys."""
        slot_content1 = [{"slot_id": "main", "content_repr": "content1"}]
        slot_content2 = [{"slot_id": "main", "content_repr": "content2"}]

        key1 = ReusableBlockCache.get_cache_key(123, slot_content1)
        key2 = ReusableBlockCache.get_cache_key(123, slot_content2)

        assert key1 != key2

    def test_cache_key_same_slot_content(self):
        """Same slot content produces same cache key."""
        slot_content1 = [{"slot_id": "main", "content_repr": "same"}]
        slot_content2 = [{"slot_id": "main", "content_repr": "same"}]

        key1 = ReusableBlockCache.get_cache_key(123, slot_content1)
        key2 = ReusableBlockCache.get_cache_key(123, slot_content2)

        assert key1 == key2


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-cache",
        }
    },
    WAGTAIL_REUSABLE_BLOCKS={"CACHE_ENABLED": True},
)
class TestReusableBlockCacheOperations(TestCase):
    """Tests for cache get/set/delete operations."""

    def setUp(self):
        """Clear cache before each test."""
        caches["default"].clear()

    def test_get_returns_none_when_not_cached(self):
        """get() returns None when key is not in cache."""
        result = ReusableBlockCache.get(999)
        assert result is None

    def test_set_and_get(self):
        """set() stores value that can be retrieved with get()."""
        ReusableBlockCache.set(123, "<p>Test content</p>")
        result = ReusableBlockCache.get(123)
        assert result == "<p>Test content</p>"

    def test_set_and_get_with_slot_content(self):
        """set() and get() work with slot content."""
        slot_content = [{"slot_id": "main", "content_repr": "test"}]
        ReusableBlockCache.set(123, "<div>With slots</div>", slot_content)
        result = ReusableBlockCache.get(123, slot_content)
        assert result == "<div>With slots</div>"

    def test_get_with_different_slot_content_returns_none(self):
        """get() with different slot content returns None."""
        slot_content1 = [{"slot_id": "main", "content_repr": "content1"}]
        slot_content2 = [{"slot_id": "main", "content_repr": "content2"}]

        ReusableBlockCache.set(123, "<div>Content 1</div>", slot_content1)
        result = ReusableBlockCache.get(123, slot_content2)
        assert result is None

    def test_delete(self):
        """delete() removes cached value."""
        ReusableBlockCache.set(123, "<p>To delete</p>")
        assert ReusableBlockCache.get(123) == "<p>To delete</p>"

        ReusableBlockCache.delete(123)
        assert ReusableBlockCache.get(123) is None

    def test_invalidate(self):
        """invalidate() removes cached value for block."""
        ReusableBlockCache.set(123, "<p>To invalidate</p>")
        assert ReusableBlockCache.get(123) == "<p>To invalidate</p>"

        ReusableBlockCache.invalidate(123)
        assert ReusableBlockCache.get(123) is None

    def test_set_with_custom_timeout(self):
        """set() accepts custom timeout."""
        # Just verify it doesn't error - actual timeout behavior
        # is hard to test without mocking time
        ReusableBlockCache.set(123, "<p>Custom timeout</p>", timeout=60)
        result = ReusableBlockCache.get(123)
        assert result == "<p>Custom timeout</p>"


class TestReusableBlockCacheDisabled:
    """Tests for cache behavior when disabled."""

    def test_get_returns_none_when_disabled(self):
        """get() returns None when cache is disabled."""
        # tests/settings.py sets CACHE_ENABLED = False
        result = ReusableBlockCache.get(123)
        assert result is None

    def test_set_does_nothing_when_disabled(self):
        """set() does nothing when cache is disabled."""
        # Should not raise error
        ReusableBlockCache.set(123, "<p>Content</p>")
        # And get should still return None
        assert ReusableBlockCache.get(123) is None


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "integration-cache",
        }
    },
    WAGTAIL_REUSABLE_BLOCKS={"CACHE_ENABLED": True},
)
class TestReusableBlockCacheIntegration(TestCase):
    """Integration tests for caching with actual blocks."""

    def setUp(self):
        """Clear cache before each test."""
        caches["default"].clear()

    def test_chooser_block_caches_render(self):
        """ReusableBlockChooserBlock caches rendered output."""
        from wagtail_reusable_blocks.blocks import ReusableBlockChooserBlock

        block_model = ReusableBlock.objects.create(
            name="Cached Block",
            content=[{"type": "rich_text", "value": "<p>Cached content</p>"}],
        )

        chooser = ReusableBlockChooserBlock()

        # First render - should cache
        html1 = chooser.render_basic(block_model)
        assert "Cached content" in html1

        # Verify it's cached
        cached = ReusableBlockCache.get(block_model.pk)
        assert cached is not None
        assert "Cached content" in cached

        # Second render - should use cache
        html2 = chooser.render_basic(block_model)
        assert html1 == html2

    def test_layout_block_caches_render(self):
        """ReusableLayoutBlock caches rendered output."""
        from wagtail_reusable_blocks.blocks import ReusableLayoutBlock

        layout_model = ReusableBlock.objects.create(
            name="Cached Layout",
            content=[{"type": "raw_html", "value": '<div data-slot="main"></div>'}],
        )

        layout_block = ReusableLayoutBlock()
        value = layout_block.to_python(
            {
                "layout": layout_model.pk,
                "slot_content": [],
            }
        )

        # First render - should cache
        html1 = layout_block.render(value)
        assert "data-slot" in html1

        # Verify it's cached (without slot content)
        cached = ReusableBlockCache.get(layout_model.pk, None)
        assert cached is not None

    def test_cache_miss_after_invalidation(self):
        """Cache miss occurs after invalidation."""
        from wagtail_reusable_blocks.blocks import ReusableBlockChooserBlock

        block_model = ReusableBlock.objects.create(
            name="To Invalidate",
            content=[{"type": "rich_text", "value": "<p>Original</p>"}],
        )

        chooser = ReusableBlockChooserBlock()

        # Render to populate cache
        chooser.render_basic(block_model)
        assert ReusableBlockCache.get(block_model.pk) is not None

        # Invalidate
        ReusableBlockCache.invalidate(block_model.pk)
        assert ReusableBlockCache.get(block_model.pk) is None

    def test_clear_all(self):
        """clear_all() clears all cache entries."""
        # Set multiple cache entries
        ReusableBlockCache.set(1, "<p>Content 1</p>")
        ReusableBlockCache.set(2, "<p>Content 2</p>")
        assert ReusableBlockCache.get(1) is not None
        assert ReusableBlockCache.get(2) is not None

        # Clear all
        ReusableBlockCache.clear_all()

        # Verify all entries are cleared
        assert ReusableBlockCache.get(1) is None
        assert ReusableBlockCache.get(2) is None

    def test_layout_block_cache_hit(self):
        """ReusableLayoutBlock uses cached value on second render."""
        from wagtail_reusable_blocks.blocks import ReusableLayoutBlock

        layout_model = ReusableBlock.objects.create(
            name="Layout for Cache Hit",
            content=[
                {"type": "raw_html", "value": '<div data-slot="main">Default</div>'}
            ],
        )

        layout_block = ReusableLayoutBlock()
        value = layout_block.to_python(
            {
                "layout": layout_model.pk,
                "slot_content": [],
            }
        )

        # First render - populates cache
        html1 = layout_block.render(value)
        assert "data-slot" in html1

        # Verify it's cached
        cached = ReusableBlockCache.get(layout_model.pk, None)
        assert cached is not None

        # Second render - should use cache (cache hit path)
        html2 = layout_block.render(value)
        assert html1 == html2

    def test_layout_block_cache_hit_with_slot_content(self):
        """ReusableLayoutBlock cache hit works with slot content."""
        from wagtail_reusable_blocks.blocks import ReusableLayoutBlock

        layout_model = ReusableBlock.objects.create(
            name="Layout with Slots",
            content=[
                {"type": "raw_html", "value": '<div data-slot="main">Default</div>'}
            ],
        )

        layout_block = ReusableLayoutBlock()
        value = layout_block.to_python(
            {
                "layout": layout_model.pk,
                "slot_content": [
                    {
                        "type": "slot_fill",
                        "value": {
                            "slot_id": "main",
                            "content": [
                                {"type": "rich_text", "value": "<p>Filled</p>"}
                            ],
                        },
                    }
                ],
            }
        )

        # First render - populates cache
        html1 = layout_block.render(value)
        assert "Filled" in html1

        # Second render - should use cache (cache hit path with slot content)
        html2 = layout_block.render(value)
        assert html1 == html2
