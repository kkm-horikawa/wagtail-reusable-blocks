"""Tests for cache invalidation signals and views (Issue #68)."""

from unittest.mock import Mock

from django.contrib.auth.models import User
from django.core.cache import caches
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse

from wagtail_reusable_blocks.cache import ReusableBlockCache
from wagtail_reusable_blocks.models import ReusableBlock
from wagtail_reusable_blocks.views.cache import (
    clear_all_cache_view,
    clear_block_cache_view,
)
from wagtail_reusable_blocks.wagtail_hooks import (
    global_admin_js,
    register_clear_cache_button,
)


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "signal-test-cache",
        }
    },
    WAGTAIL_REUSABLE_BLOCKS={"CACHE_ENABLED": True},
)
class TestCacheInvalidationSignals(TestCase):
    """Tests for cache invalidation on model save/delete."""

    def setUp(self):
        """Clear cache before each test."""
        caches["default"].clear()

    def test_cache_invalidated_on_save(self):
        """Cache is invalidated when a ReusableBlock is saved."""
        # Create a block and cache some content
        block = ReusableBlock.objects.create(
            name="Test Block",
            content=[{"type": "rich_text", "value": "<p>Original</p>"}],
        )

        # Manually cache content
        ReusableBlockCache.set(block.pk, "<p>Cached content</p>")
        assert ReusableBlockCache.get(block.pk) == "<p>Cached content</p>"

        # Save the block (triggers post_save signal)
        block.name = "Updated Block"
        block.save()

        # Cache should be invalidated
        assert ReusableBlockCache.get(block.pk) is None

    def test_cache_invalidated_on_delete(self):
        """Cache is cleaned up when a ReusableBlock is deleted."""
        # Create a block and cache some content
        block = ReusableBlock.objects.create(
            name="To Delete",
            content=[{"type": "rich_text", "value": "<p>To delete</p>"}],
        )
        block_pk = block.pk

        # Manually cache content
        ReusableBlockCache.set(block_pk, "<p>Cached content</p>")
        assert ReusableBlockCache.get(block_pk) == "<p>Cached content</p>"

        # Delete the block (triggers post_delete signal)
        block.delete()

        # Cache should be cleaned up
        assert ReusableBlockCache.get(block_pk) is None

    def test_cache_invalidated_on_create(self):
        """Cache invalidation doesn't error on new block creation."""
        # Creating a block also triggers post_save, should not error
        block = ReusableBlock.objects.create(
            name="New Block",
            content=[{"type": "rich_text", "value": "<p>New</p>"}],
        )

        # No cached content should exist for new block
        assert ReusableBlockCache.get(block.pk) is None


class TestCacheInvalidationSignalsDisabled(TestCase):
    """Tests for cache invalidation behavior when caching is disabled."""

    def test_signal_does_nothing_when_cache_disabled(self):
        """Signals do nothing when caching is disabled."""
        # tests/settings.py sets CACHE_ENABLED = False
        # This should not error even though cache is disabled
        block = ReusableBlock.objects.create(
            name="Test Block",
            content=[{"type": "rich_text", "value": "<p>Test</p>"}],
        )

        # Updating should not error
        block.name = "Updated"
        block.save()

        # Deleting should not error
        block.delete()


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "view-test-cache",
        }
    },
    WAGTAIL_REUSABLE_BLOCKS={"CACHE_ENABLED": True},
)
class TestClearCacheViews(TestCase):
    """Tests for cache clear views."""

    def setUp(self):
        """Set up test user and clear cache."""
        caches["default"].clear()
        self.user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_clear_block_cache_view(self):
        """Clear cache view clears cache for specific block."""
        block = ReusableBlock.objects.create(
            name="Test Block",
            content=[{"type": "rich_text", "value": "<p>Test</p>"}],
        )

        # Cache some content
        ReusableBlockCache.set(block.pk, "<p>Cached</p>")
        assert ReusableBlockCache.get(block.pk) == "<p>Cached</p>"

        # Call the clear cache view
        response = self.client.post(
            reverse("wagtail_reusable_blocks:clear_block_cache", args=[block.pk])
        )

        # Should redirect
        assert response.status_code == 302

        # Cache should be cleared
        assert ReusableBlockCache.get(block.pk) is None

    def test_clear_all_cache_view(self):
        """Clear all cache view clears all block caches."""
        block1 = ReusableBlock.objects.create(
            name="Block 1",
            content=[{"type": "rich_text", "value": "<p>1</p>"}],
        )
        block2 = ReusableBlock.objects.create(
            name="Block 2",
            content=[{"type": "rich_text", "value": "<p>2</p>"}],
        )

        # Cache some content
        ReusableBlockCache.set(block1.pk, "<p>Cached 1</p>")
        ReusableBlockCache.set(block2.pk, "<p>Cached 2</p>")
        assert ReusableBlockCache.get(block1.pk) is not None
        assert ReusableBlockCache.get(block2.pk) is not None

        # Call the clear all cache view
        response = self.client.post(reverse("wagtail_reusable_blocks:clear_all_cache"))

        # Should redirect
        assert response.status_code == 302

        # All caches should be cleared
        assert ReusableBlockCache.get(block1.pk) is None
        assert ReusableBlockCache.get(block2.pk) is None

    def test_clear_block_cache_view_requires_post(self):
        """Clear cache view only accepts POST requests."""
        block = ReusableBlock.objects.create(
            name="Test Block",
            content=[{"type": "rich_text", "value": "<p>Test</p>"}],
        )

        response = self.client.get(
            reverse("wagtail_reusable_blocks:clear_block_cache", args=[block.pk])
        )

        # Should return 405 Method Not Allowed
        assert response.status_code == 405

    def test_clear_all_cache_view_requires_post(self):
        """Clear all cache view only accepts POST requests."""
        response = self.client.get(reverse("wagtail_reusable_blocks:clear_all_cache"))

        # Should return 405 Method Not Allowed
        assert response.status_code == 405

    def test_clear_block_cache_view_returns_404_for_nonexistent_block(self):
        """Clear cache view returns 404 for non-existent block."""
        response = self.client.post(
            reverse("wagtail_reusable_blocks:clear_block_cache", args=[99999])
        )

        assert response.status_code == 404


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "perm-test-cache",
        }
    },
    WAGTAIL_REUSABLE_BLOCKS={"CACHE_ENABLED": True},
)
class TestClearCacheViewsPermission(TestCase):
    """Tests for cache clear view permissions."""

    def setUp(self):
        """Set up test user without permissions."""
        self.user = User.objects.create_user(
            username="regular",
            email="regular@example.com",
            password="password",
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_clear_block_cache_view_requires_permission(self):
        """Clear cache view requires change_reusableblock permission."""
        block = ReusableBlock.objects.create(
            name="Test Block",
            content=[{"type": "rich_text", "value": "<p>Test</p>"}],
        )

        response = self.client.post(
            reverse("wagtail_reusable_blocks:clear_block_cache", args=[block.pk])
        )

        # Should be permission denied (403 or redirect to login)
        assert response.status_code in (302, 403)
        if response.status_code == 302:
            # Redirects to login page
            assert "login" in response.url

    def test_clear_all_cache_view_requires_permission(self):
        """Clear all cache view requires change_reusableblock permission."""
        response = self.client.post(reverse("wagtail_reusable_blocks:clear_all_cache"))

        # Should be permission denied (403 or redirect to login)
        assert response.status_code in (302, 403)
        if response.status_code == 302:
            # Redirects to login page
            assert "login" in response.url


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "direct-perm-test-cache",
        }
    },
    WAGTAIL_REUSABLE_BLOCKS={"CACHE_ENABLED": True},
)
class TestClearCacheViewsPermissionDirect(TestCase):
    """Tests for permission denied path in cache clear views using direct calls."""

    def setUp(self):
        """Set up request factory and session."""
        from django.contrib.sessions.backends.db import SessionStore

        self.factory = RequestFactory()
        self.session = SessionStore()
        self.session.create()

    def _setup_request(self, request):
        """Add session and messages to request."""
        from django.contrib.messages.storage.fallback import FallbackStorage

        request.session = self.session
        request._messages = FallbackStorage(request)
        return request

    def test_clear_block_cache_view_permission_denied(self):
        """Clear cache view returns permission denied for user without permission."""
        block = ReusableBlock.objects.create(
            name="Test Block",
            content=[{"type": "rich_text", "value": "<p>Test</p>"}],
        )

        # Create request with user that doesn't have permission
        request = self.factory.post(f"/blocks/{block.pk}/clear-cache/")
        request.user = Mock()
        request.user.has_perm = Mock(return_value=False)
        self._setup_request(request)

        response = clear_block_cache_view(request, block.pk)

        # Should return permission denied response
        assert response.status_code in (302, 403)

    def test_clear_all_cache_view_permission_denied(self):
        """Clear all cache view returns permission denied for user without permission."""
        # Create request with user that doesn't have permission
        request = self.factory.post("/clear-all-cache/")
        request.user = Mock()
        request.user.has_perm = Mock(return_value=False)
        self._setup_request(request)

        response = clear_all_cache_view(request)

        # Should return permission denied response
        assert response.status_code in (302, 403)


class TestClearCacheButtonHook:
    """Tests for the clear cache button hook."""

    def test_returns_empty_for_non_reusable_block(self):
        """Hook returns empty list for non-ReusableBlock snippets."""

        class OtherSnippet:
            pk = 1

        result = register_clear_cache_button(OtherSnippet(), None)
        assert result == []

    def test_returns_empty_when_cache_disabled(self):
        """Hook returns empty list when caching is disabled."""
        # tests/settings.py sets CACHE_ENABLED = False
        block = ReusableBlock(pk=1, name="Test")
        result = register_clear_cache_button(block, None)
        assert result == []

    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "hook-test-cache",
            }
        },
        WAGTAIL_REUSABLE_BLOCKS={"CACHE_ENABLED": True},
    )
    def test_returns_button_when_cache_enabled(self):
        """Hook returns button when caching is enabled."""
        block = ReusableBlock(pk=123, name="Test")
        result = register_clear_cache_button(block, None)
        assert len(result) == 1
        assert result[0].label == "Clear Cache"
        assert "123" in result[0].url


class TestGlobalAdminJsHook:
    """Tests for the global admin JS hook."""

    def test_returns_empty_when_cache_disabled(self):
        """Hook returns empty string when caching is disabled."""
        # tests/settings.py sets CACHE_ENABLED = False
        result = global_admin_js()
        assert result == ""

    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "js-hook-test-cache",
            }
        },
        WAGTAIL_REUSABLE_BLOCKS={"CACHE_ENABLED": True},
    )
    def test_returns_javascript_when_cache_enabled(self):
        """Hook returns JavaScript when caching is enabled."""
        result = global_admin_js()
        assert "<script>" in result
        assert "data-clear-cache-url" in result


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "message-test-cache",
        }
    },
    WAGTAIL_REUSABLE_BLOCKS={"CACHE_ENABLED": True},
)
class TestClearCacheViewMessages(TestCase):
    """Tests for success messages in cache clear views."""

    def setUp(self):
        """Set up test user and clear cache."""
        caches["default"].clear()
        self.user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_clear_block_cache_shows_success_message(self):
        """Clear block cache view shows success message."""
        block = ReusableBlock.objects.create(
            name="Test Block",
            content=[{"type": "rich_text", "value": "<p>Test</p>"}],
        )

        response = self.client.post(
            reverse("wagtail_reusable_blocks:clear_block_cache", args=[block.pk]),
            follow=True,
        )

        # Check for success message
        messages_list = list(response.context.get("messages", []))
        assert len(messages_list) >= 1
        assert "Cache cleared" in str(messages_list[0])

    def test_clear_all_cache_shows_success_message(self):
        """Clear all cache view shows success message."""
        response = self.client.post(
            reverse("wagtail_reusable_blocks:clear_all_cache"),
            follow=True,
        )

        # Check for success message
        messages_list = list(response.context.get("messages", []))
        assert len(messages_list) >= 1
        assert "cache entries have been cleared" in str(messages_list[0])
