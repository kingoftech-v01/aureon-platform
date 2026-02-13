"""
Views and ViewSets for the emails app API.
"""

from rest_framework import viewsets, mixins, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, Count

from .models import EmailAccount, EmailMessage, EmailAttachment, EmailTemplate
from .serializers import (
    EmailAccountSerializer,
    EmailMessageListSerializer,
    EmailMessageDetailSerializer,
    EmailMessageCreateSerializer,
    EmailAttachmentSerializer,
    EmailTemplateSerializer,
)


class EmailAccountViewSet(viewsets.ModelViewSet):
    """
    ViewSet for EmailAccount CRUD operations.

    list: Get list of email accounts
    retrieve: Get email account details
    create: Create a new email account
    update: Update an email account
    partial_update: Partially update an email account
    destroy: Delete an email account
    """

    queryset = EmailAccount.objects.all()
    serializer_class = EmailAccountSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['provider', 'is_active']
    ordering = ['-is_default', '-created_at']

    def get_queryset(self):
        """Filter queryset to current user's accounts unless staff."""
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        return queryset

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """
        Set this email account as the default for the user.

        Unsets the current default and sets this account as default.
        """
        account = self.get_object()

        # Unset all other defaults for this user
        EmailAccount.objects.filter(
            user=account.user, is_default=True
        ).update(is_default=False)

        # Set this as default
        account.is_default = True
        account.save(update_fields=['is_default', 'updated_at'])

        serializer = self.get_serializer(account)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """
        Test the connection for this email account.

        Attempts to verify the email account configuration is valid.
        """
        account = self.get_object()

        # Placeholder for actual connection testing logic
        # In production, this would attempt to connect to the SMTP server,
        # verify Gmail OAuth tokens, test Outlook API, or validate SES credentials
        return Response({
            'status': 'success',
            'message': f'Connection test for {account.email_address} completed.',
            'provider': account.provider,
        })


class EmailMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for EmailMessage CRUD operations.

    list: Get list of email messages with filtering and search
    retrieve: Get email message details
    create: Create a new email message (draft)
    update: Update an email message
    partial_update: Partially update an email message
    destroy: Delete an email message
    """

    queryset = EmailMessage.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['account', 'status', 'direction', 'client', 'is_read']
    search_fields = ['subject', 'body_text', 'from_email']
    ordering_fields = ['created_at', 'sent_at', 'received_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return EmailMessageListSerializer
        elif self.action == 'create':
            return EmailMessageCreateSerializer
        return EmailMessageDetailSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(account__user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        """Set from_email and direction on create."""
        account = serializer.validated_data['account']
        serializer.save(
            from_email=account.email_address,
            direction=EmailMessage.OUTBOUND,
        )

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """
        Send the email message.

        Sets status to SENT and records the sent_at timestamp.
        """
        email_message = self.get_object()

        if email_message.status not in [EmailMessage.DRAFT, EmailMessage.QUEUED]:
            return Response(
                {'detail': f'Cannot send email with status "{email_message.status}".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        email_message.status = EmailMessage.SENT
        email_message.sent_at = timezone.now()
        email_message.save(update_fields=['status', 'sent_at', 'updated_at'])

        serializer = EmailMessageDetailSerializer(email_message)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Mark the email message as read.
        """
        email_message = self.get_object()
        email_message.is_read = True
        email_message.save(update_fields=['is_read', 'updated_at'])

        serializer = EmailMessageDetailSerializer(email_message)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_unread(self, request, pk=None):
        """
        Mark the email message as unread.
        """
        email_message = self.get_object()
        email_message.is_read = False
        email_message.save(update_fields=['is_read', 'updated_at'])

        serializer = EmailMessageDetailSerializer(email_message)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get email statistics.

        Returns counts for total, sent, received, drafts, and unread messages.
        """
        queryset = self.filter_queryset(self.get_queryset())

        stats = {
            'total': queryset.count(),
            'sent': queryset.filter(direction=EmailMessage.OUTBOUND, status=EmailMessage.SENT).count(),
            'received': queryset.filter(direction=EmailMessage.INBOUND).count(),
            'drafts': queryset.filter(status=EmailMessage.DRAFT).count(),
            'unread': queryset.filter(is_read=False).count(),
        }

        return Response(stats)


class EmailAttachmentViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for EmailAttachment operations.

    Supports create, retrieve, destroy, and list (no update).
    """

    queryset = EmailAttachment.objects.all()
    serializer_class = EmailAttachmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['email']

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(email__account__user=self.request.user)
        return queryset


class EmailTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for EmailTemplate CRUD operations.

    list: Get list of email templates with filtering and search
    retrieve: Get email template details
    create: Create a new email template
    update: Update an email template
    partial_update: Partially update an email template
    destroy: Delete an email template
    """

    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'subject']
    ordering = ['name']

    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """
        Preview a rendered email template.

        Accepts a context dictionary in the request body and returns
        the template with variables substituted.
        """
        template = self.get_object()
        context = request.data.get('context', {})

        rendered = template.render(context)

        return Response({
            'name': template.name,
            'category': template.category,
            'rendered_subject': rendered['subject'],
            'rendered_body_text': rendered['body_text'],
            'rendered_body_html': rendered['body_html'],
        })
