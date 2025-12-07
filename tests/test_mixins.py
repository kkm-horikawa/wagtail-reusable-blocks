"""Tests for Wagtail mixins integration in ReusableBlock."""

import pytest
from wagtail.models import (
    DraftStateMixin,
    LockableMixin,
    PreviewableMixin,
    RevisionMixin,
    WorkflowMixin,
)

from wagtail_reusable_blocks.models import ReusableBlock


class TestReusableBlockMixins:
    """Tests for mixin inheritance."""

    def test_inherits_revision_mixin(self):
        """ReusableBlock inherits RevisionMixin."""
        assert issubclass(ReusableBlock, RevisionMixin)

    def test_inherits_draft_state_mixin(self):
        """ReusableBlock inherits DraftStateMixin."""
        assert issubclass(ReusableBlock, DraftStateMixin)

    def test_inherits_lockable_mixin(self):
        """ReusableBlock inherits LockableMixin."""
        assert issubclass(ReusableBlock, LockableMixin)

    def test_inherits_workflow_mixin(self):
        """ReusableBlock inherits WorkflowMixin."""
        assert issubclass(ReusableBlock, WorkflowMixin)

    def test_inherits_previewable_mixin(self):
        """ReusableBlock inherits PreviewableMixin."""
        assert issubclass(ReusableBlock, PreviewableMixin)


class TestDraftStateFields:
    """Tests for DraftStateMixin fields."""

    def test_has_live_field(self):
        """ReusableBlock has live field from DraftStateMixin."""
        assert hasattr(ReusableBlock, "live")
        field = ReusableBlock._meta.get_field("live")
        assert field.default is True

    def test_has_has_unpublished_changes_field(self):
        """ReusableBlock has has_unpublished_changes field."""
        assert hasattr(ReusableBlock, "has_unpublished_changes")
        field = ReusableBlock._meta.get_field("has_unpublished_changes")
        assert field.default is False

    def test_has_first_published_at_field(self):
        """ReusableBlock has first_published_at field."""
        assert hasattr(ReusableBlock, "first_published_at")

    def test_has_last_published_at_field(self):
        """ReusableBlock has last_published_at field."""
        assert hasattr(ReusableBlock, "last_published_at")

    def test_has_go_live_at_field(self):
        """ReusableBlock has go_live_at field for scheduled publishing."""
        assert hasattr(ReusableBlock, "go_live_at")

    def test_has_expire_at_field(self):
        """ReusableBlock has expire_at field for scheduled expiry."""
        assert hasattr(ReusableBlock, "expire_at")


class TestRevisionFields:
    """Tests for RevisionMixin fields."""

    def test_has_latest_revision_field(self):
        """ReusableBlock has latest_revision field."""
        assert hasattr(ReusableBlock, "latest_revision")

    def test_has_revisions_property(self):
        """ReusableBlock has revisions property."""
        assert hasattr(ReusableBlock, "revisions")

    def test_has_revisions_generic_relation(self):
        """ReusableBlock has _revisions GenericRelation."""
        assert hasattr(ReusableBlock, "_revisions")


class TestLockableFields:
    """Tests for LockableMixin fields."""

    def test_has_locked_field(self):
        """ReusableBlock has locked field."""
        assert hasattr(ReusableBlock, "locked")
        field = ReusableBlock._meta.get_field("locked")
        assert field.default is False

    def test_has_locked_by_field(self):
        """ReusableBlock has locked_by field."""
        assert hasattr(ReusableBlock, "locked_by")

    def test_has_locked_at_field(self):
        """ReusableBlock has locked_at field."""
        assert hasattr(ReusableBlock, "locked_at")


class TestWorkflowFields:
    """Tests for WorkflowMixin fields."""

    def test_has_workflow_states_generic_relation(self):
        """ReusableBlock has workflow_states GenericRelation."""
        assert hasattr(ReusableBlock, "workflow_states")


class TestPreviewableMixin:
    """Tests for PreviewableMixin methods."""

    def test_has_get_preview_template_method(self):
        """ReusableBlock has get_preview_template method."""
        assert hasattr(ReusableBlock, "get_preview_template")
        assert callable(ReusableBlock.get_preview_template)

    def test_has_get_preview_context_method(self):
        """ReusableBlock has get_preview_context method."""
        assert hasattr(ReusableBlock, "get_preview_context")
        assert callable(ReusableBlock.get_preview_context)


@pytest.mark.django_db
class TestDraftStateBehavior:
    """Tests for DraftStateMixin behavior."""

    def test_new_block_is_live_by_default(self):
        """New ReusableBlock is live by default."""
        block = ReusableBlock.objects.create(name="Test Block")
        assert block.live is True

    def test_new_block_has_no_unpublished_changes(self):
        """New ReusableBlock has no unpublished changes."""
        block = ReusableBlock.objects.create(name="Test Block")
        assert block.has_unpublished_changes is False


@pytest.mark.django_db
class TestLockableBehavior:
    """Tests for LockableMixin behavior."""

    def test_new_block_is_not_locked(self):
        """New ReusableBlock is not locked by default."""
        block = ReusableBlock.objects.create(name="Test Block")
        assert block.locked is False
        assert block.locked_by is None
        assert block.locked_at is None


@pytest.mark.django_db
class TestPreviewBehavior:
    """Tests for PreviewableMixin behavior."""

    def test_get_preview_template_returns_setting(self, settings):
        """get_preview_template returns template from PREVIEW_TEMPLATE setting."""
        settings.WAGTAIL_REUSABLE_BLOCKS = {
            "PREVIEW_TEMPLATE": "custom/preview.html",
        }
        block = ReusableBlock(name="Test Block")
        assert block.get_preview_template() == "custom/preview.html"

    def test_get_preview_context_includes_block(self):
        """get_preview_context includes block in context."""
        block = ReusableBlock(name="Test Block")
        context = block.get_preview_context()
        assert "block" in context
        assert context["block"] is block
