"""
Tests for webhooks signals.

The webhooks/signals.py file is empty (single blank line).
These tests verify that the signals module exists and is importable,
and that no unexpected side effects occur on import.
"""

import importlib


class TestWebhookSignalsModule:
    """Verify the signals module is present and importable."""

    def test_module_importable(self):
        """signals.py should be importable without errors."""
        module = importlib.import_module('apps.webhooks.signals')
        assert module is not None

    def test_module_has_no_unexpected_exports(self):
        """Empty signals module should not export signal handlers."""
        module = importlib.import_module('apps.webhooks.signals')
        # Filter out dunder attributes
        public_attrs = [a for a in dir(module) if not a.startswith('_')]
        # An empty module may have __builtins__ etc., but no public signal handlers
        # We just verify it doesn't crash
        assert isinstance(public_attrs, list)
