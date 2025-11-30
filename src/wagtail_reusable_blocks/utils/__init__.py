"""Utilities for wagtail-reusable-blocks."""

from .slot_detection import SlotInfo, detect_slots_from_html

__all__ = ["detect_slots_from_html", "SlotInfo"]
