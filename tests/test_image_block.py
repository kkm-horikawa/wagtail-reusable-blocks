"""Tests for ImageBlock."""

import pytest
from wagtail.images.tests.utils import get_test_image_file

from wagtail_reusable_blocks.blocks import ImageBlock


class TestImageBlock:
    """Tests for ImageBlock functionality."""

    @pytest.fixture
    def block(self):
        """Create an ImageBlock instance."""
        return ImageBlock()

    def test_initialization(self, block):
        """ImageBlock initializes with correct child blocks."""
        assert "image" in block.child_blocks

    def test_meta_template(self, block):
        """Block has correct default template."""
        assert block.meta.template == "wagtail_reusable_blocks/blocks/image.html"

    def test_meta_icon(self, block):
        """Block has correct default icon."""
        assert block.meta.icon == "image"

    def test_meta_label(self, block):
        """Block has correct default label."""
        assert block.meta.label == "Image"

    def test_import_from_blocks_module(self):
        """ImageBlock can be imported from blocks module."""
        from wagtail_reusable_blocks.blocks import ImageBlock

        assert ImageBlock is not None

    def test_import_from_package(self):
        """ImageBlock can be imported from package root."""
        from wagtail_reusable_blocks import ImageBlock

        assert ImageBlock is not None


class TestImageBlockRendering:
    """Tests for ImageBlock rendering."""

    @pytest.fixture
    def block(self):
        """Create an ImageBlock instance."""
        return ImageBlock()

    @pytest.fixture
    def test_image(self, db):
        """Create a test image."""
        from wagtail.images.models import Image

        return Image.objects.create(
            title="Test Image",
            file=get_test_image_file(),
        )

    def test_render_basic(self, block, test_image):
        """Renders image with picture tag."""
        value = block.to_python({"image": test_image.pk})
        html = block.render(value)

        assert "<picture" in html or "<img" in html

    def test_render_includes_lazy_loading(self, block, test_image):
        """Rendered image has lazy loading attribute."""
        value = block.to_python({"image": test_image.pk})
        html = block.render(value)

        assert 'loading="lazy"' in html

    def test_render_includes_decoding_async(self, block, test_image):
        """Rendered image has async decoding attribute."""
        value = block.to_python({"image": test_image.pk})
        html = block.render(value)

        assert 'decoding="async"' in html


class TestImageBlockInSlotContent:
    """Tests for ImageBlock availability in SlotContentStreamBlock."""

    def test_image_block_in_slot_content(self):
        """ImageBlock is available in SlotContentStreamBlock."""
        from wagtail_reusable_blocks.blocks.slot_fill import SlotContentStreamBlock

        stream_block = SlotContentStreamBlock()
        child_block_names = list(stream_block.child_blocks.keys())

        assert "image" in child_block_names

    def test_image_block_type_in_slot_content(self):
        """SlotContentStreamBlock uses ImageBlock for image type."""
        from wagtail_reusable_blocks.blocks.slot_fill import SlotContentStreamBlock

        stream_block = SlotContentStreamBlock()
        image_block = stream_block.child_blocks.get("image")

        assert isinstance(image_block, ImageBlock)
