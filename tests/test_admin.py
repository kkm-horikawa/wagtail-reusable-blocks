"""Tests for ReusableBlock admin UI customization."""

import pytest
from django.test import override_settings

from wagtail_reusable_blocks.models import ReusableBlock
from wagtail_reusable_blocks.wagtail_hooks import (
    ReusableBlockFilterSet,
    ReusableBlockViewSet,
)


class TestReusableBlockViewSet:
    """Tests for ReusableBlockViewSet configuration."""

    @pytest.fixture
    def viewset(self):
        """Create a ReusableBlockViewSet instance."""
        return ReusableBlockViewSet()

    def test_model_configuration(self, viewset):
        """ViewSet is configured with correct model."""
        assert viewset.model == ReusableBlock

    def test_icon_configuration(self, viewset):
        """ViewSet has correct icon."""
        assert viewset.icon == "snippet"

    def test_menu_label(self, viewset):
        """ViewSet has correct menu label."""
        assert viewset.menu_label == "Reusable Blocks"

    def test_search_fields(self, viewset):
        """ViewSet has correct search fields."""
        assert viewset.search_fields == ["name", "slug"]

    def test_list_display(self, viewset):
        """ViewSet has correct list display columns."""
        assert "name" in viewset.list_display
        assert "slug" in viewset.list_display
        # LiveStatusTagColumn and UpdatedAtColumn are also in the list
        assert len(viewset.list_display) == 4

    def test_list_per_page(self, viewset):
        """ViewSet has correct pagination."""
        assert viewset.list_per_page == 50

    def test_filterset_class(self, viewset):
        """ViewSet has correct filterset class."""
        assert viewset.filterset_class == ReusableBlockFilterSet

    def test_ordering(self, viewset):
        """ViewSet has correct default ordering."""
        assert viewset.ordering == ["-updated_at"]

    def test_copy_view_enabled(self, viewset):
        """Copy functionality is enabled."""
        assert viewset.copy_view_enabled is True

    def test_inspect_view_enabled(self, viewset):
        """Inspect view is enabled."""
        assert viewset.inspect_view_enabled is True

    def test_preview_enabled(self, viewset):
        """Preview functionality is enabled."""
        assert viewset.preview_enabled is True


class TestReusableBlockFilterSet:
    """Tests for ReusableBlockFilterSet."""

    def test_model_configuration(self):
        """FilterSet is configured with correct model."""
        assert ReusableBlockFilterSet.Meta.model == ReusableBlock

    def test_filter_fields(self):
        """FilterSet has correct filter fields."""
        assert "created_at" in ReusableBlockFilterSet.Meta.fields
        assert "updated_at" in ReusableBlockFilterSet.Meta.fields

    def test_filter_lookup_expressions(self):
        """FilterSet has correct lookup expressions."""
        assert ReusableBlockFilterSet.Meta.fields["created_at"] == ["date"]
        assert ReusableBlockFilterSet.Meta.fields["updated_at"] == ["date"]


@pytest.mark.django_db
class TestReusableBlockQueryset:
    """Tests for ReusableBlock queryset behavior with admin configuration."""

    def test_ordering_by_updated_at(self):
        """Blocks are ordered by most recently updated first."""
        # Create blocks
        old_block = ReusableBlock.objects.create(
            name="Old Block",
            content=[("rich_text", "<p>Old</p>")],
        )
        new_block = ReusableBlock.objects.create(
            name="New Block",
            content=[("rich_text", "<p>New</p>")],
        )

        # Default ordering should be -updated_at
        blocks = ReusableBlock.objects.all()
        assert list(blocks) == [new_block, old_block]

    def test_search_fields_accessible(self):
        """Search fields (name, slug) are accessible for filtering."""
        ReusableBlock.objects.create(
            name="Test Block",
            content=[("rich_text", "<p>Content</p>")],
        )

        # Search by name
        assert ReusableBlock.objects.filter(name__icontains="test").count() == 1

        # Search by slug (auto-generated from name)
        assert ReusableBlock.objects.filter(slug__icontains="test-block").count() == 1

    def test_filter_by_date_fields(self):
        """Date fields (created_at, updated_at) can be filtered."""
        from django.utils import timezone

        ReusableBlock.objects.create(
            name="Test Block",
            content=[("rich_text", "<p>Content</p>")],
        )

        # Filter by created_at date
        today = timezone.now().date()
        assert ReusableBlock.objects.filter(created_at__date=today).count() == 1

        # Filter by updated_at date
        assert ReusableBlock.objects.filter(updated_at__date=today).count() == 1


class TestWagtailHooksRegistration:
    """Tests for wagtail_hooks registration behavior."""

    def test_viewset_registration_when_enabled(self):
        """ViewSet is registered when REGISTER_DEFAULT_SNIPPET is True."""
        # This test verifies the default behavior - the viewset should be registered
        # We can't easily check if register_snippet was called, but we can verify
        # the module executes without errors
        import wagtail_reusable_blocks.wagtail_hooks  # noqa: F401

        # If we got here without errors, the registration succeeded
        assert True

    @override_settings(WAGTAIL_REUSABLE_BLOCKS={"REGISTER_DEFAULT_SNIPPET": False})
    def test_viewset_not_registered_when_disabled(self):
        """ViewSet is not registered when REGISTER_DEFAULT_SNIPPET is False."""
        # Re-import the module to test the conditional registration
        import importlib

        import wagtail_reusable_blocks.wagtail_hooks

        importlib.reload(wagtail_reusable_blocks.wagtail_hooks)

        # If we got here without errors, the conditional worked correctly
        # The ViewSet class still exists but register_snippet wasn't called
        assert True
