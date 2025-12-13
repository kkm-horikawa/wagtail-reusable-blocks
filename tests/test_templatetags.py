"""Tests for template tags and filters."""

from unittest.mock import MagicMock

from wagtail_reusable_blocks.templatetags.reusable_blocks_tags import is_gif


class TestIsGifFilter:
    """Tests for the is_gif template filter."""

    def test_gif_file_returns_true(self):
        """is_gif returns True for .gif files."""
        image = MagicMock()
        image.file.name = "test_image.gif"
        assert is_gif(image) is True

    def test_gif_uppercase_returns_true(self):
        """is_gif returns True for .GIF files (uppercase)."""
        image = MagicMock()
        image.file.name = "test_image.GIF"
        assert is_gif(image) is True

    def test_png_file_returns_false(self):
        """is_gif returns False for .png files."""
        image = MagicMock()
        image.file.name = "test_image.png"
        assert is_gif(image) is False

    def test_jpg_file_returns_false(self):
        """is_gif returns False for .jpg files."""
        image = MagicMock()
        image.file.name = "test_image.jpg"
        assert is_gif(image) is False

    def test_none_image_returns_false(self):
        """is_gif returns False for None."""
        assert is_gif(None) is False

    def test_image_without_file_returns_false(self):
        """is_gif returns False when image has no file attribute."""
        image = MagicMock(spec=[])
        assert is_gif(image) is False

    def test_image_with_none_file_returns_false(self):
        """is_gif returns False when image.file is None."""
        image = MagicMock()
        image.file = None
        assert is_gif(image) is False

    def test_gif_in_subdirectory(self):
        """is_gif works with files in subdirectories."""
        image = MagicMock()
        image.file.name = "images/2024/01/animation.gif"
        assert is_gif(image) is True
