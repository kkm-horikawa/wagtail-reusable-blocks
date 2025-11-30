"""Tests for view endpoints (Issue #48)."""

import json

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from wagtail_reusable_blocks.models import ReusableBlock

User = get_user_model()


@pytest.fixture
def admin_user():
    """Create an admin user with Wagtail admin access."""
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="password"
    )


@pytest.fixture
def admin_client(client, admin_user):
    """Client logged in as admin user."""
    client.login(username="admin", password="password")
    return client


class TestBlockSlotsView:
    """Tests for block_slots_view API endpoint."""

    @pytest.mark.django_db
    def test_get_slots_from_block(self, admin_client):
        """Returns slots from a ReusableBlock."""
        # Create a block with slots
        block = ReusableBlock.objects.create(
            name="Test Layout",
            content=[
                {
                    "type": "raw_html",
                    "value": """
                    <div data-slot="header" data-slot-label="Header Area">
                        <h1>Default Header</h1>
                    </div>
                    <div data-slot="main"></div>
                    """,
                }
            ],
        )

        # Call the API
        url = reverse("wagtail_reusable_blocks:block_slots", args=[block.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        data = json.loads(response.content)

        assert "slots" in data
        assert len(data["slots"]) == 2

        # Check header slot
        header_slot = [s for s in data["slots"] if s["id"] == "header"][0]
        assert header_slot["label"] == "Header Area"
        assert header_slot["has_default"] is True

        # Check main slot
        main_slot = [s for s in data["slots"] if s["id"] == "main"][0]
        assert main_slot["label"] == "main"
        assert main_slot["has_default"] is False

    @pytest.mark.django_db
    def test_block_not_found(self, admin_client):
        """Returns 404 for non-existent block."""
        url = reverse("wagtail_reusable_blocks:block_slots", args=[99999])
        response = admin_client.get(url)

        assert response.status_code == 404

    @pytest.mark.django_db
    def test_empty_slots(self, admin_client):
        """Returns empty slots list for block without slots."""
        block = ReusableBlock.objects.create(
            name="No Slots",
            content=[{"type": "rich_text", "value": "<p>Just content</p>"}],
        )

        url = reverse("wagtail_reusable_blocks:block_slots", args=[block.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["slots"] == []

    @pytest.mark.django_db
    def test_post_not_allowed(self, admin_client):
        """POST method is not allowed."""
        block = ReusableBlock.objects.create(
            name="Test",
            content=[{"type": "rich_text", "value": "<p>Test</p>"}],
        )

        url = reverse("wagtail_reusable_blocks:block_slots", args=[block.pk])
        response = admin_client.post(url)

        assert response.status_code == 405  # Method Not Allowed

    @pytest.mark.django_db
    def test_complex_layout_slots(self, admin_client):
        """Returns all slots from complex nested layout."""
        block = ReusableBlock.objects.create(
            name="Complex Layout",
            content=[
                {
                    "type": "raw_html",
                    "value": """
                    <div class="layout">
                        <header data-slot="header"></header>
                        <div class="content">
                            <aside data-slot="sidebar">
                                <div>Default sidebar</div>
                            </aside>
                            <main data-slot="main"></main>
                        </div>
                        <footer data-slot="footer" data-slot-label="Footer Area">
                            <p>Default footer</p>
                        </footer>
                    </div>
                    """,
                }
            ],
        )

        url = reverse("wagtail_reusable_blocks:block_slots", args=[block.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        data = json.loads(response.content)

        assert len(data["slots"]) == 4
        slot_ids = {s["id"] for s in data["slots"]}
        assert slot_ids == {"header", "sidebar", "main", "footer"}

        # Verify footer has custom label
        footer_slot = [s for s in data["slots"] if s["id"] == "footer"][0]
        assert footer_slot["label"] == "Footer Area"
        assert footer_slot["has_default"] is True


class TestURLConfiguration:
    """Tests for URL configuration."""

    def test_block_slots_url_reverses(self):
        """block_slots URL can be reversed."""
        url = reverse("wagtail_reusable_blocks:block_slots", args=[123])
        # URL doesn't include /admin prefix in reverse (added by Wagtail hook)
        assert "/reusable-blocks/blocks/123/slots/" in url

    @pytest.mark.django_db
    def test_url_is_accessible(self, admin_client):
        """URL is accessible (returns 404 for non-existent block, not URL error)."""
        url = reverse("wagtail_reusable_blocks:block_slots", args=[99999])
        response = admin_client.get(url)

        # Should return 404 (block not found), not 404 (URL not found)
        assert response.status_code == 404
