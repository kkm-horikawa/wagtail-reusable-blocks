"""Django app configuration for wagtail-reusable-blocks."""

import logging

from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class WagtailReusableBlocksConfig(AppConfig):
    """Configuration class for wagtail-reusable-blocks."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "wagtail_reusable_blocks"
    verbose_name = "Wagtail Reusable Blocks"

    def ready(self) -> None:
        """
        Perform initialization when Django starts.

        Validates settings configuration and registers default snippet if enabled.
        """
        self._validate_settings()
        self._register_default_snippet()

    def _validate_settings(self) -> None:
        """Validate settings configuration."""
        from .conf import get_setting

        # Validate TEMPLATE setting
        template = get_setting("TEMPLATE")
        if template is not None and not isinstance(template, str):
            raise ImproperlyConfigured(
                "WAGTAIL_REUSABLE_BLOCKS['TEMPLATE'] must be a string. "
                f"Got {type(template).__name__} instead."
            )

    def _register_default_snippet(self) -> None:
        """Register default ReusableBlock as snippet if enabled."""
        from django.core.exceptions import ImproperlyConfigured

        from .conf import get_setting

        if get_setting("REGISTER_DEFAULT_SNIPPET"):
            from wagtail.snippets.models import register_snippet

            from .models import ReusableBlock

            # Only register if not already registered
            try:
                register_snippet(ReusableBlock)
            except ImproperlyConfigured:
                # Already registered - this is fine in tests
                pass
