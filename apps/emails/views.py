"""
Views for the emails app.

Re-exports from views_api for convenience.
"""

from .views_api import (  # noqa: F401
    EmailAccountViewSet,
    EmailMessageViewSet,
    EmailAttachmentViewSet,
    EmailTemplateViewSet,
)
