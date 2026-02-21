"""Integration tests for admin JS config injection via insert_global_admin_js hook."""

import json

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse

User = get_user_model()


@pytest.fixture
def admin_user(db):
    """Create a superuser for Wagtail admin access."""
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="password",
    )


@pytest.fixture
def admin_client(client, admin_user):
    """Django test client logged in as admin."""
    client.login(username="admin", password="password")
    return client


def _wagtail_admin_url():
    """Return the Wagtail admin dashboard URL via reverse."""
    return reverse("wagtailadmin_home")


def _extract_config(html: str) -> dict:
    """Extract wagtailReusableBlocksConfig JSON from HTML content."""
    marker = "window.wagtailReusableBlocksConfig="
    start = html.index(marker) + len(marker)
    end = html.index(";</script>", start)
    return json.loads(html[start:end])


@pytest.mark.django_db
class TestSlotUrlConfigInjection:
    """Verify that the wagtailReusableBlocksConfig script tag is injected into admin pages."""

    def test_admin_page_contains_reusable_blocks_config_script(self, admin_client):
        """Admin dashboard HTML contains the wagtailReusableBlocksConfig script.

        Purpose: Verify that the insert_global_admin_js hook injects a script tag
                 with the slots URL template into Wagtail admin pages, so that
                 slot-chooser.js can resolve the correct API endpoint.
        Category: Normal flow
        Technique: Middleware behavior (Wagtail hook pipeline)
        Integration target: GET wagtailadmin_home -> insert_global_admin_js hook -> HTML
        Test data:
        - Superuser with full admin access
        Verification scenario:
        1. Log in as admin and fetch the Wagtail admin dashboard
        2. Assert the response contains window.wagtailReusableBlocksConfig
        """
        response = admin_client.get(_wagtail_admin_url())

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "window.wagtailReusableBlocksConfig=" in content

    def test_injected_config_contains_valid_slots_url_template(self, admin_client):
        """Injected config script contains a valid slotsUrlTemplate with placeholder.

        Purpose: Verify that the slotsUrlTemplate in the injected config is a
                 properly formed URL containing the __BLOCK_ID__ placeholder,
                 ensuring JavaScript can substitute real block IDs at runtime.
        Category: Normal flow
        Technique: API endpoint (URL resolution via hook)
        Integration target: GET wagtailadmin_home -> insert_global_admin_js -> reverse() -> HTML
        Test data:
        - Superuser with full admin access
        Verification scenario:
        1. Fetch the admin dashboard
        2. Extract the JSON config from the script tag
        3. Assert slotsUrlTemplate contains __BLOCK_ID__ placeholder
        4. Assert the URL path includes the expected route segments
        """
        response = admin_client.get(_wagtail_admin_url())
        content = response.content.decode("utf-8")
        config = _extract_config(content)

        assert "slotsUrlTemplate" in config
        url_template = config["slotsUrlTemplate"]
        assert "__BLOCK_ID__" in url_template
        assert "/reusable-blocks/blocks/" in url_template
        assert url_template.endswith("/slots/")

    def test_injected_url_template_resolves_to_working_endpoint(
        self,
        admin_client,
    ):
        """URL template from config resolves to the block_slots endpoint.

        Purpose: Verify end-to-end that replacing __BLOCK_ID__ in the injected
                 URL template with a real block ID produces a URL that reaches
                 the block_slots_view and returns 404 (block not found), proving
                 the URL routing is correct.
        Category: Normal flow
        Technique: API endpoint (full round-trip)
        Integration target: GET admin -> extract URL -> GET slots endpoint -> 404
        Test data:
        - Superuser with full admin access
        - Non-existent block ID (99999)
        Verification scenario:
        1. Fetch the admin dashboard and extract slotsUrlTemplate
        2. Replace __BLOCK_ID__ with a non-existent block ID
        3. Fetch the resulting URL
        4. Assert 404 (block not found, not URL routing error)
        """
        response = admin_client.get(_wagtail_admin_url())
        content = response.content.decode("utf-8")
        config = _extract_config(content)

        url = config["slotsUrlTemplate"].replace("__BLOCK_ID__", "99999")
        slots_response = admin_client.get(url)

        assert slots_response.status_code == 404

    def test_injected_url_matches_django_reverse(self, admin_client):
        """Injected URL template matches what Django reverse() produces.

        Purpose: Verify that the URL template injected via the hook is consistent
                 with Django's URL resolution, ensuring no mismatch between
                 server-side routing and client-side URL construction.
        Category: Normal flow
        Technique: API endpoint (URL consistency)
        Integration target: GET admin -> extract URL -> compare with reverse()
        Test data:
        - Superuser with full admin access
        Verification scenario:
        1. Fetch the admin dashboard and extract slotsUrlTemplate
        2. Compute the expected URL via Django reverse() with a known block ID
        3. Replace __BLOCK_ID__ in template with the same ID
        4. Assert both URLs match
        """
        response = admin_client.get(_wagtail_admin_url())
        content = response.content.decode("utf-8")
        config = _extract_config(content)

        block_id = 42
        url_from_template = config["slotsUrlTemplate"].replace(
            "__BLOCK_ID__",
            str(block_id),
        )
        url_from_reverse = reverse(
            "wagtail_reusable_blocks:block_slots",
            kwargs={"block_id": block_id},
        )

        assert url_from_template == url_from_reverse

    def test_unauthenticated_user_redirected_to_login(self, client):
        """Unauthenticated request to admin is redirected to login.

        Purpose: Verify that unauthenticated users cannot access the admin page
                 and therefore do not receive the injected config script.
        Category: Error flow
        Technique: Authentication/authorization
        Integration target: GET wagtailadmin_home -> redirect to login
        Test data:
        - Unauthenticated client (no login)
        Verification scenario:
        1. Fetch the admin dashboard without logging in
        2. Assert redirect (302) to login page
        """
        response = client.get(_wagtail_admin_url(), follow=False)

        assert response.status_code == 302

    @override_settings(WAGTAILADMIN_BASE_URL="https://custom.example.com")
    def test_config_injected_with_custom_wagtail_base_url(self, admin_client):
        """Config is injected even when WAGTAILADMIN_BASE_URL is customized.

        Purpose: Verify the hook works correctly regardless of Wagtail base URL
                 configuration, which was the original issue (#218).
        Category: Normal flow (boundary)
        Technique: Middleware behavior (settings variation)
        Integration target: GET admin -> hook with custom WAGTAILADMIN_BASE_URL -> HTML
        Test data:
        - Custom WAGTAILADMIN_BASE_URL setting
        - Superuser with full admin access
        Verification scenario:
        1. Override WAGTAILADMIN_BASE_URL
        2. Fetch admin dashboard
        3. Assert config script is still present with correct URL template
        """
        response = admin_client.get(_wagtail_admin_url())

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        config = _extract_config(content)

        assert "__BLOCK_ID__" in config["slotsUrlTemplate"]
