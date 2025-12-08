"""Django app configuration for wagtail-reusable-blocks."""

import logging

from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class WagtailReusableBlocksConfig(AppConfig):
    """Configuration class for wagtail-reusable-blocks."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "wagtail_reusable_blocks"
    verbose_name = _("Wagtail Reusable Blocks")

    def ready(self) -> None:
        """
        Perform initialization when Django starts.

        Validates settings configuration and registers signal handlers.
        Note: ReusableBlock snippet registration is now handled in wagtail_hooks.py
        """
        self._validate_settings()
        self._register_signals()

    def _register_signals(self) -> None:
        """Register signal handlers for cache invalidation."""
        # Import signals module to register handlers
        # This must be done in ready() to ensure models are loaded
        from . import signals  # noqa: F401

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
