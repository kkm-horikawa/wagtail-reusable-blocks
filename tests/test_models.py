"""Tests for ReusableBlock model."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from wagtail_reusable_blocks.models import ReusableBlock


class TestReusableBlockCreation:
    """Tests for creating ReusableBlock instances."""

    @pytest.mark.django_db
    def test_create_with_valid_data(self):
        """ReusableBlock can be created with valid name and content."""
        block = ReusableBlock.objects.create(
            name="Test Block",
            content=[
                {"type": "rich_text", "value": "<p>Test content</p>"},
            ],
        )

        assert block.name == "Test Block"
        assert block.slug == "test-block"
        assert len(block.content) == 1
        assert block.created_at is not None
        assert block.updated_at is not None

    @pytest.mark.django_db
    def test_slug_auto_generated_from_name(self):
        """Slug is automatically generated from name."""
        block = ReusableBlock.objects.create(name="My Awesome Block")

        assert block.slug == "my-awesome-block"

    @pytest.mark.django_db
    def test_slug_with_special_characters(self):
        """Special characters in name are removed from slug."""
        block = ReusableBlock.objects.create(name="Header & Footer <test>")

        assert block.slug == "header-footer-test"

    @pytest.mark.django_db
    def test_empty_content_allowed(self):
        """ReusableBlock can be created with empty content."""
        block = ReusableBlock.objects.create(name="Empty Block", content=[])

        assert block.name == "Empty Block"
        assert len(block.content) == 0

    @pytest.mark.django_db
    def test_multiple_content_blocks(self):
        """ReusableBlock can contain multiple content blocks."""
        block = ReusableBlock.objects.create(
            name="Multi Block",
            content=[
                {"type": "rich_text", "value": "<p>First</p>"},
                {"type": "raw_html", "value": "<div>Second</div>"},
                {"type": "rich_text", "value": "<p>Third</p>"},
            ],
        )

        assert len(block.content) == 3


class TestReusableBlockSlugUniqueness:
    """Tests for slug uniqueness constraints."""

    @pytest.mark.django_db
    def test_duplicate_slug_raises_integrity_error(self):
        """Creating blocks with duplicate slugs raises IntegrityError."""
        ReusableBlock.objects.create(name="Test Block", slug="test-block")

        with pytest.raises(IntegrityError):
            ReusableBlock.objects.create(name="Another Block", slug="test-block")

    @pytest.mark.django_db
    def test_duplicate_names_with_same_slug(self):
        """Two blocks with same name generate duplicate slugs and fail."""
        ReusableBlock.objects.create(name="Test Block")

        with pytest.raises(IntegrityError):
            ReusableBlock.objects.create(name="Test Block")

    @pytest.mark.django_db
    def test_manual_slug_override(self):
        """Manually set slug is respected."""
        block = ReusableBlock.objects.create(
            name="Test Block",
            slug="custom-slug",
        )

        assert block.slug == "custom-slug"

    @pytest.mark.django_db
    def test_slug_can_be_blank_on_creation(self):
        """Slug can be left blank and will be auto-generated."""
        # This simulates creating via admin form without providing slug
        block = ReusableBlock(name="New Block")
        block.save()

        assert block.slug == "new-block"


class TestReusableBlockValidation:
    """Tests for model validation."""

    @pytest.mark.django_db
    def test_empty_name_raises_validation_error(self):
        """Empty name raises ValidationError."""
        block = ReusableBlock(name="", content=[])

        with pytest.raises(ValidationError):
            block.full_clean()

    @pytest.mark.django_db
    def test_name_max_length(self):
        """Name respects max length constraint."""
        long_name = "a" * 256  # Exceeds MAX_NAME_LENGTH (255)
        block = ReusableBlock(name=long_name, content=[])

        with pytest.raises(ValidationError):
            block.full_clean()

    @pytest.mark.django_db
    def test_name_within_max_length(self):
        """Name within max length is valid."""
        valid_name = "a" * 255  # Exactly MAX_NAME_LENGTH
        block = ReusableBlock.objects.create(name=valid_name, content=[])

        # Verify it was created successfully
        assert block.pk is not None
        assert len(block.name) == 255


class TestReusableBlockTimestamps:
    """Tests for created_at and updated_at timestamps."""

    @pytest.mark.django_db
    def test_created_at_set_on_creation(self):
        """created_at is set when block is created."""
        before = timezone.now()
        block = ReusableBlock.objects.create(name="Test Block")
        after = timezone.now()

        assert before <= block.created_at <= after

    @pytest.mark.django_db
    def test_updated_at_changes_on_save(self):
        """updated_at changes when block is updated."""
        block = ReusableBlock.objects.create(name="Test Block")
        original_updated_at = block.updated_at
        original_created_at = block.created_at

        # Small delay to ensure time difference
        import time

        time.sleep(0.01)

        block.name = "Updated Block"
        block.save()

        assert block.updated_at > original_updated_at
        assert block.created_at == original_created_at

    @pytest.mark.django_db
    def test_created_at_unchanged_on_update(self):
        """created_at remains unchanged when block is updated."""
        block = ReusableBlock.objects.create(name="Test Block")
        original_created_at = block.created_at

        import time

        time.sleep(0.01)

        block.name = "Updated Block"
        block.save()

        assert block.created_at == original_created_at


class TestReusableBlockStringRepresentation:
    """Tests for __str__ method."""

    @pytest.mark.django_db
    def test_str_returns_name(self):
        """__str__ returns the block name."""
        block = ReusableBlock.objects.create(name="My Block")

        assert str(block) == "My Block"


class TestReusableBlockOrdering:
    """Tests for default ordering."""

    @pytest.mark.django_db
    def test_default_ordering_by_updated_at_desc(self):
        """Blocks are ordered by updated_at descending by default."""
        block1 = ReusableBlock.objects.create(name="Block 1")

        import time

        time.sleep(0.01)

        block2 = ReusableBlock.objects.create(name="Block 2")

        time.sleep(0.01)

        block3 = ReusableBlock.objects.create(name="Block 3")

        blocks = list(ReusableBlock.objects.all())

        assert blocks[0] == block3  # Most recently updated
        assert blocks[1] == block2
        assert blocks[2] == block1  # Least recently updated


class TestReusableBlockCRUD:
    """Tests for Create, Read, Update, Delete operations."""

    @pytest.mark.django_db
    def test_create_and_retrieve(self):
        """Block can be created and retrieved from database."""
        block = ReusableBlock.objects.create(name="Test Block")

        retrieved = ReusableBlock.objects.get(pk=block.pk)

        assert retrieved.name == "Test Block"
        assert retrieved.slug == "test-block"

    @pytest.mark.django_db
    def test_update_block(self):
        """Block can be updated."""
        block = ReusableBlock.objects.create(name="Original Name")

        block.name = "Updated Name"
        block.save()

        retrieved = ReusableBlock.objects.get(pk=block.pk)

        assert retrieved.name == "Updated Name"

    @pytest.mark.django_db
    def test_delete_block(self):
        """Block can be deleted."""
        block = ReusableBlock.objects.create(name="Test Block")
        block_id = block.pk

        block.delete()

        assert not ReusableBlock.objects.filter(pk=block_id).exists()

    @pytest.mark.django_db
    def test_filter_by_slug(self):
        """Blocks can be filtered by slug."""
        ReusableBlock.objects.create(name="Block 1", slug="block-1")
        ReusableBlock.objects.create(name="Block 2", slug="block-2")

        result = ReusableBlock.objects.filter(slug="block-1")

        assert result.count() == 1
        assert result.first().name == "Block 1"  # type: ignore[union-attr]
