"""
Integration services for Aureon SaaS Platform.

Each service encapsulates the logic for syncing data with a specific
third-party provider. Services read credentials from the Integration
model and log every sync run via IntegrationSyncLog.
"""

import logging
import time
from abc import ABC, abstractmethod
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import Integration, IntegrationSyncLog

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base service
# ---------------------------------------------------------------------------

class BaseIntegrationService(ABC):
    """Abstract base for all integration services."""

    service_type: str = ''

    def __init__(self, integration: Integration):
        self.integration = integration

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def sync(self, sync_type='full'):
        """Run a sync and record it in the sync log."""
        log = IntegrationSyncLog.objects.create(
            integration=self.integration,
            status='running',
            metadata={'sync_type': sync_type},
        )
        start = time.monotonic()

        try:
            result = self.execute_sync(sync_type)
            elapsed = int((time.monotonic() - start) * 1000)

            log.status = 'success'
            log.records_synced = result.get('records_synced', 0)
            log.duration_ms = elapsed
            log.metadata.update(result.get('metadata', {}))
            log.completed_at = timezone.now()
            log.save()

            # Update integration tracking fields
            self.integration.last_sync_at = timezone.now()
            self.integration.last_sync_status = 'success'
            self.integration.last_sync_error = ''
            self.integration.save(update_fields=[
                'last_sync_at', 'last_sync_status', 'last_sync_error', 'updated_at',
            ])

            logger.info(
                f"Sync completed for {self.integration.name}: "
                f"{log.records_synced} records in {elapsed}ms"
            )
            return log

        except Exception as exc:
            elapsed = int((time.monotonic() - start) * 1000)
            log.status = 'error'
            log.errors = [str(exc)]
            log.duration_ms = elapsed
            log.completed_at = timezone.now()
            log.save()

            self.integration.last_sync_at = timezone.now()
            self.integration.last_sync_status = 'error'
            self.integration.last_sync_error = str(exc)
            self.integration.save(update_fields=[
                'last_sync_at', 'last_sync_status', 'last_sync_error', 'updated_at',
            ])

            logger.exception(f"Sync failed for {self.integration.name}")
            raise

    def test_connection(self):
        """Verify the integration credentials work."""
        try:
            result = self._test_connection()
            return {'connected': True, **result}
        except Exception as exc:
            return {'connected': False, 'error': str(exc)}

    def refresh_token(self):
        """Refresh OAuth token if expired."""
        if not self.integration.needs_reauth:
            return False

        try:
            new_tokens = self._refresh_token()
            self.integration.access_token = new_tokens['access_token']
            if 'refresh_token' in new_tokens:
                self.integration.refresh_token = new_tokens['refresh_token']
            if 'expires_in' in new_tokens:
                self.integration.token_expires_at = (
                    timezone.now() + timedelta(seconds=new_tokens['expires_in'])
                )
            self.integration.save(update_fields=[
                'access_token', 'refresh_token', 'token_expires_at', 'updated_at',
            ])
            logger.info(f"Token refreshed for {self.integration.name}")
            return True
        except Exception:
            logger.exception(f"Token refresh failed for {self.integration.name}")
            self.integration.status = Integration.ERROR
            self.integration.save(update_fields=['status', 'updated_at'])
            raise

    # ------------------------------------------------------------------
    # Abstract methods — implemented per service
    # ------------------------------------------------------------------

    @abstractmethod
    def execute_sync(self, sync_type='full'):
        """Execute the actual sync. Return dict with records_synced, metadata."""

    @abstractmethod
    def _test_connection(self):
        """Test the connection. Return dict or raise."""

    @abstractmethod
    def _refresh_token(self):
        """Refresh OAuth tokens. Return dict with access_token, etc."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_headers(self):
        return {
            'Authorization': f'Bearer {self.integration.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def _api_url(self, path=''):
        base = self.integration.config.get('api_url', '')
        return f"{base.rstrip('/')}/{path.lstrip('/')}" if path else base


# ---------------------------------------------------------------------------
# QuickBooks
# ---------------------------------------------------------------------------

class QuickBooksService(BaseIntegrationService):
    """QuickBooks Online integration for syncing invoices, payments, clients."""

    service_type = 'quickbooks'

    def execute_sync(self, sync_type='full'):
        import requests

        headers = self._get_headers()
        company_id = self.integration.config.get('company_id', '')
        base = self.integration.config.get(
            'api_url',
            'https://quickbooks.api.intuit.com/v3',
        )

        records_synced = 0
        metadata = {}

        # --- Sync clients → QuickBooks Customers --------------------------
        from apps.clients.models import Client

        clients = Client.objects.all()
        if sync_type == 'incremental' and self.integration.last_sync_at:
            clients = clients.filter(updated_at__gte=self.integration.last_sync_at)

        for client in clients:
            payload = {
                'DisplayName': client.name if hasattr(client, 'name') else str(client),
                'PrimaryEmailAddr': {'Address': getattr(client, 'email', '')},
                'CompanyName': getattr(client, 'company_name', ''),
            }
            resp = requests.post(
                f"{base}/company/{company_id}/customer",
                json=payload, headers=headers, timeout=30,
            )
            if resp.ok:
                records_synced += 1
            else:
                logger.warning(f"QuickBooks customer sync failed: {resp.text}")

        metadata['customers_synced'] = records_synced

        # --- Sync invoices ------------------------------------------------
        from apps.invoicing.models import Invoice

        invoices = Invoice.objects.filter(status__in=['sent', 'paid'])
        if sync_type == 'incremental' and self.integration.last_sync_at:
            invoices = invoices.filter(updated_at__gte=self.integration.last_sync_at)

        invoice_count = 0
        for invoice in invoices:
            payload = {
                'DocNumber': getattr(invoice, 'invoice_number', str(invoice.id)),
                'TotalAmt': float(getattr(invoice, 'total_amount', 0)),
                'DueDate': str(getattr(invoice, 'due_date', '')),
            }
            resp = requests.post(
                f"{base}/company/{company_id}/invoice",
                json=payload, headers=headers, timeout=30,
            )
            if resp.ok:
                invoice_count += 1
                records_synced += 1
            else:
                logger.warning(f"QuickBooks invoice sync failed: {resp.text}")

        metadata['invoices_synced'] = invoice_count

        # --- Sync payments ------------------------------------------------
        from apps.payments.models import Payment

        payments = Payment.objects.filter(status='succeeded')
        if sync_type == 'incremental' and self.integration.last_sync_at:
            payments = payments.filter(updated_at__gte=self.integration.last_sync_at)

        payment_count = 0
        for payment in payments:
            payload = {
                'TotalAmt': float(getattr(payment, 'amount', 0)),
                'PaymentMethodRef': {'value': 'stripe'},
            }
            resp = requests.post(
                f"{base}/company/{company_id}/payment",
                json=payload, headers=headers, timeout=30,
            )
            if resp.ok:
                payment_count += 1
                records_synced += 1
            else:
                logger.warning(f"QuickBooks payment sync failed: {resp.text}")

        metadata['payments_synced'] = payment_count
        return {'records_synced': records_synced, 'metadata': metadata}

    def _test_connection(self):
        import requests

        company_id = self.integration.config.get('company_id', '')
        base = self.integration.config.get(
            'api_url',
            'https://quickbooks.api.intuit.com/v3',
        )
        resp = requests.get(
            f"{base}/company/{company_id}/companyinfo/{company_id}",
            headers=self._get_headers(), timeout=15,
        )
        resp.raise_for_status()
        return {'company': resp.json().get('CompanyInfo', {}).get('CompanyName', '')}

    def _refresh_token(self):
        import requests

        token_url = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer'
        resp = requests.post(token_url, data={
            'grant_type': 'refresh_token',
            'refresh_token': self.integration.refresh_token,
            'client_id': self.integration.config.get('client_id', ''),
            'client_secret': self.integration.config.get('client_secret', ''),
        }, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return {
            'access_token': data['access_token'],
            'refresh_token': data.get('refresh_token', self.integration.refresh_token),
            'expires_in': data.get('expires_in', 3600),
        }


# ---------------------------------------------------------------------------
# Xero
# ---------------------------------------------------------------------------

class XeroService(BaseIntegrationService):
    """Xero accounting integration for syncing invoices, payments, clients."""

    service_type = 'xero'

    def execute_sync(self, sync_type='full'):
        import requests

        headers = self._get_headers()
        tenant_id = self.integration.config.get('tenant_id', '')
        headers['Xero-Tenant-Id'] = tenant_id
        base = 'https://api.xero.com/api.xro/2.0'

        records_synced = 0
        metadata = {}

        # --- Sync clients → Xero Contacts ---------------------------------
        from apps.clients.models import Client

        clients = Client.objects.all()
        if sync_type == 'incremental' and self.integration.last_sync_at:
            clients = clients.filter(updated_at__gte=self.integration.last_sync_at)

        contact_count = 0
        for client in clients:
            payload = {
                'Contacts': [{
                    'Name': client.name if hasattr(client, 'name') else str(client),
                    'EmailAddress': getattr(client, 'email', ''),
                }]
            }
            resp = requests.post(
                f"{base}/Contacts", json=payload, headers=headers, timeout=30,
            )
            if resp.ok:
                contact_count += 1
                records_synced += 1
            else:
                logger.warning(f"Xero contact sync failed: {resp.text}")

        metadata['contacts_synced'] = contact_count

        # --- Sync invoices ------------------------------------------------
        from apps.invoicing.models import Invoice

        invoices = Invoice.objects.filter(status__in=['sent', 'paid'])
        if sync_type == 'incremental' and self.integration.last_sync_at:
            invoices = invoices.filter(updated_at__gte=self.integration.last_sync_at)

        invoice_count = 0
        for invoice in invoices:
            payload = {
                'Invoices': [{
                    'Type': 'ACCREC',
                    'InvoiceNumber': getattr(invoice, 'invoice_number', str(invoice.id)),
                    'Status': 'AUTHORISED' if invoice.status == 'sent' else 'PAID',
                    'Total': float(getattr(invoice, 'total_amount', 0)),
                    'DueDate': str(getattr(invoice, 'due_date', '')),
                    'CurrencyCode': getattr(invoice, 'currency', 'USD'),
                }]
            }
            resp = requests.post(
                f"{base}/Invoices", json=payload, headers=headers, timeout=30,
            )
            if resp.ok:
                invoice_count += 1
                records_synced += 1
            else:
                logger.warning(f"Xero invoice sync failed: {resp.text}")

        metadata['invoices_synced'] = invoice_count

        # --- Sync payments ------------------------------------------------
        from apps.payments.models import Payment

        payments = Payment.objects.filter(status='succeeded')
        if sync_type == 'incremental' and self.integration.last_sync_at:
            payments = payments.filter(updated_at__gte=self.integration.last_sync_at)

        payment_count = 0
        for payment in payments:
            payload = {
                'Payments': [{
                    'Amount': float(getattr(payment, 'amount', 0)),
                    'Date': str(getattr(payment, 'created_at', timezone.now()).date()),
                }]
            }
            resp = requests.post(
                f"{base}/Payments", json=payload, headers=headers, timeout=30,
            )
            if resp.ok:
                payment_count += 1
                records_synced += 1
            else:
                logger.warning(f"Xero payment sync failed: {resp.text}")

        metadata['payments_synced'] = payment_count
        return {'records_synced': records_synced, 'metadata': metadata}

    def _test_connection(self):
        import requests

        tenant_id = self.integration.config.get('tenant_id', '')
        headers = self._get_headers()
        headers['Xero-Tenant-Id'] = tenant_id
        resp = requests.get(
            'https://api.xero.com/api.xro/2.0/Organisation',
            headers=headers, timeout=15,
        )
        resp.raise_for_status()
        orgs = resp.json().get('Organisations', [])
        return {'organisation': orgs[0]['Name'] if orgs else ''}

    def _refresh_token(self):
        import requests

        resp = requests.post('https://identity.xero.com/connect/token', data={
            'grant_type': 'refresh_token',
            'refresh_token': self.integration.refresh_token,
            'client_id': self.integration.config.get('client_id', ''),
            'client_secret': self.integration.config.get('client_secret', ''),
        }, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return {
            'access_token': data['access_token'],
            'refresh_token': data.get('refresh_token', self.integration.refresh_token),
            'expires_in': data.get('expires_in', 1800),
        }


# ---------------------------------------------------------------------------
# Google Calendar
# ---------------------------------------------------------------------------

class GoogleCalendarService(BaseIntegrationService):
    """Google Calendar integration for syncing contract milestones as events."""

    service_type = 'google_calendar'

    def execute_sync(self, sync_type='full'):
        import requests

        headers = self._get_headers()
        calendar_id = self.integration.config.get('calendar_id', 'primary')
        base = 'https://www.googleapis.com/calendar/v3'

        records_synced = 0
        metadata = {}

        # Sync contract milestones as calendar events
        from apps.contracts.models import Contract

        contracts = Contract.objects.filter(status='active')
        if sync_type == 'incremental' and self.integration.last_sync_at:
            contracts = contracts.filter(updated_at__gte=self.integration.last_sync_at)

        for contract in contracts:
            milestones = contract.milestones.all() if hasattr(contract, 'milestones') else []
            for milestone in milestones:
                due = getattr(milestone, 'due_date', None)
                if not due:
                    continue

                event = {
                    'summary': f"[Aureon] {getattr(milestone, 'title', str(milestone))}",
                    'description': (
                        f"Contract: {contract}\n"
                        f"Amount: {getattr(milestone, 'amount', 'N/A')}"
                    ),
                    'start': {'date': str(due)},
                    'end': {'date': str(due)},
                    'reminders': {'useDefault': True},
                }

                resp = requests.post(
                    f"{base}/calendars/{calendar_id}/events",
                    json=event, headers=headers, timeout=15,
                )
                if resp.ok:
                    records_synced += 1
                else:
                    logger.warning(f"Google Calendar event sync failed: {resp.text}")

        metadata['events_synced'] = records_synced

        # Sync invoice due dates
        from apps.invoicing.models import Invoice

        invoices = Invoice.objects.filter(status__in=['sent', 'viewed'])
        if sync_type == 'incremental' and self.integration.last_sync_at:
            invoices = invoices.filter(updated_at__gte=self.integration.last_sync_at)

        invoice_events = 0
        for invoice in invoices:
            due = getattr(invoice, 'due_date', None)
            if not due:
                continue

            event = {
                'summary': f"[Aureon] Invoice {getattr(invoice, 'invoice_number', '')} due",
                'description': f"Amount: {getattr(invoice, 'total_amount', 'N/A')}",
                'start': {'date': str(due)},
                'end': {'date': str(due)},
                'reminders': {
                    'useDefault': False,
                    'overrides': [{'method': 'email', 'minutes': 1440}],
                },
            }

            resp = requests.post(
                f"{base}/calendars/{calendar_id}/events",
                json=event, headers=headers, timeout=15,
            )
            if resp.ok:
                invoice_events += 1
                records_synced += 1
            else:
                logger.warning(f"Google Calendar invoice event sync failed: {resp.text}")

        metadata['invoice_events_synced'] = invoice_events
        return {'records_synced': records_synced, 'metadata': metadata}

    def _test_connection(self):
        import requests

        calendar_id = self.integration.config.get('calendar_id', 'primary')
        resp = requests.get(
            f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}",
            headers=self._get_headers(), timeout=15,
        )
        resp.raise_for_status()
        return {'calendar': resp.json().get('summary', '')}

    def _refresh_token(self):
        import requests

        resp = requests.post('https://oauth2.googleapis.com/token', data={
            'grant_type': 'refresh_token',
            'refresh_token': self.integration.refresh_token,
            'client_id': self.integration.config.get('client_id', ''),
            'client_secret': self.integration.config.get('client_secret', ''),
        }, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return {
            'access_token': data['access_token'],
            'expires_in': data.get('expires_in', 3600),
        }


# ---------------------------------------------------------------------------
# Microsoft Outlook Calendar
# ---------------------------------------------------------------------------

class OutlookCalendarService(BaseIntegrationService):
    """Microsoft Outlook Calendar integration for contract milestones."""

    service_type = 'outlook'

    def execute_sync(self, sync_type='full'):
        import requests

        headers = self._get_headers()
        base = 'https://graph.microsoft.com/v1.0/me'

        records_synced = 0
        metadata = {}

        from apps.contracts.models import Contract

        contracts = Contract.objects.filter(status='active')
        if sync_type == 'incremental' and self.integration.last_sync_at:
            contracts = contracts.filter(updated_at__gte=self.integration.last_sync_at)

        for contract in contracts:
            milestones = contract.milestones.all() if hasattr(contract, 'milestones') else []
            for milestone in milestones:
                due = getattr(milestone, 'due_date', None)
                if not due:
                    continue

                event = {
                    'subject': f"[Aureon] {getattr(milestone, 'title', str(milestone))}",
                    'body': {
                        'contentType': 'Text',
                        'content': (
                            f"Contract: {contract}\n"
                            f"Amount: {getattr(milestone, 'amount', 'N/A')}"
                        ),
                    },
                    'start': {
                        'dateTime': f"{due}T09:00:00",
                        'timeZone': 'UTC',
                    },
                    'end': {
                        'dateTime': f"{due}T09:30:00",
                        'timeZone': 'UTC',
                    },
                    'isAllDay': True,
                }

                resp = requests.post(
                    f"{base}/events",
                    json=event, headers=headers, timeout=15,
                )
                if resp.ok:
                    records_synced += 1
                else:
                    logger.warning(f"Outlook event sync failed: {resp.text}")

        metadata['events_synced'] = records_synced

        # Sync invoice due dates
        from apps.invoicing.models import Invoice

        invoices = Invoice.objects.filter(status__in=['sent', 'viewed'])
        if sync_type == 'incremental' and self.integration.last_sync_at:
            invoices = invoices.filter(updated_at__gte=self.integration.last_sync_at)

        invoice_events = 0
        for invoice in invoices:
            due = getattr(invoice, 'due_date', None)
            if not due:
                continue

            event = {
                'subject': f"[Aureon] Invoice {getattr(invoice, 'invoice_number', '')} due",
                'body': {
                    'contentType': 'Text',
                    'content': f"Amount: {getattr(invoice, 'total_amount', 'N/A')}",
                },
                'start': {
                    'dateTime': f"{due}T09:00:00",
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': f"{due}T09:30:00",
                    'timeZone': 'UTC',
                },
                'isAllDay': True,
                'isReminderOn': True,
                'reminderMinutesBeforeStart': 1440,
            }

            resp = requests.post(
                f"{base}/events",
                json=event, headers=headers, timeout=15,
            )
            if resp.ok:
                invoice_events += 1
                records_synced += 1
            else:
                logger.warning(f"Outlook invoice event sync failed: {resp.text}")

        metadata['invoice_events_synced'] = invoice_events
        return {'records_synced': records_synced, 'metadata': metadata}

    def _test_connection(self):
        import requests

        resp = requests.get(
            'https://graph.microsoft.com/v1.0/me',
            headers=self._get_headers(), timeout=15,
        )
        resp.raise_for_status()
        return {'user': resp.json().get('displayName', '')}

    def _refresh_token(self):
        import requests

        tenant_id = self.integration.config.get('tenant_id', 'common')
        resp = requests.post(
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
            data={
                'grant_type': 'refresh_token',
                'refresh_token': self.integration.refresh_token,
                'client_id': self.integration.config.get('client_id', ''),
                'client_secret': self.integration.config.get('client_secret', ''),
                'scope': 'https://graph.microsoft.com/.default',
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            'access_token': data['access_token'],
            'refresh_token': data.get('refresh_token', self.integration.refresh_token),
            'expires_in': data.get('expires_in', 3600),
        }


# ---------------------------------------------------------------------------
# Slack
# ---------------------------------------------------------------------------

class SlackService(BaseIntegrationService):
    """Slack integration for posting notifications on key events."""

    service_type = 'slack'

    def execute_sync(self, sync_type='full'):
        """
        For Slack, 'sync' means posting recent activity to the configured channel.
        """
        import requests

        channel = self.integration.config.get('channel', '#general')
        records_synced = 0
        metadata = {}

        # Post recent payment notifications
        from apps.payments.models import Payment

        since = self.integration.last_sync_at or (timezone.now() - timedelta(hours=24))
        payments = Payment.objects.filter(
            status='succeeded', created_at__gte=since,
        ).select_related('invoice')

        for payment in payments:
            invoice_num = getattr(payment.invoice, 'invoice_number', 'N/A') if payment.invoice else 'N/A'
            text = (
                f":white_check_mark: *Payment received*\n"
                f"Amount: {getattr(payment, 'amount', 'N/A')} "
                f"{getattr(payment, 'currency', 'USD')}\n"
                f"Invoice: {invoice_num}"
            )
            sent = self._post_message(channel, text)
            if sent:
                records_synced += 1

        metadata['payment_notifications'] = records_synced

        # Post overdue invoice alerts
        from apps.invoicing.models import Invoice

        overdue = Invoice.objects.filter(status='overdue', updated_at__gte=since)
        overdue_count = 0
        for invoice in overdue:
            text = (
                f":warning: *Invoice overdue*\n"
                f"Invoice: {getattr(invoice, 'invoice_number', str(invoice.id))}\n"
                f"Amount: {getattr(invoice, 'total_amount', 'N/A')}\n"
                f"Due: {getattr(invoice, 'due_date', 'N/A')}"
            )
            sent = self._post_message(channel, text)
            if sent:
                overdue_count += 1
                records_synced += 1

        metadata['overdue_notifications'] = overdue_count

        # Post new contract notifications
        from apps.contracts.models import Contract

        new_contracts = Contract.objects.filter(
            status='active', created_at__gte=since,
        )
        contract_count = 0
        for contract in new_contracts:
            text = (
                f":memo: *New contract signed*\n"
                f"Contract: {contract}\n"
                f"Value: {getattr(contract, 'total_value', 'N/A')}"
            )
            sent = self._post_message(channel, text)
            if sent:
                contract_count += 1
                records_synced += 1

        metadata['contract_notifications'] = contract_count
        return {'records_synced': records_synced, 'metadata': metadata}

    def _post_message(self, channel, text):
        """Post a message to Slack."""
        import requests

        token = self.integration.access_token
        resp = requests.post(
            'https://slack.com/api/chat.postMessage',
            json={'channel': channel, 'text': text},
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
            },
            timeout=10,
        )
        if resp.ok and resp.json().get('ok'):
            return True
        logger.warning(f"Slack message failed: {resp.text}")
        return False

    def _test_connection(self):
        import requests

        resp = requests.post(
            'https://slack.com/api/auth.test',
            headers={
                'Authorization': f'Bearer {self.integration.access_token}',
                'Content-Type': 'application/json',
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get('ok'):
            raise ConnectionError(data.get('error', 'Unknown Slack error'))
        return {'team': data.get('team', ''), 'user': data.get('user', '')}

    def _refresh_token(self):
        """Slack bot tokens don't expire, but handle OAuth refresh if needed."""
        # Slack bot tokens are long-lived; user tokens use standard OAuth
        if not self.integration.refresh_token:
            return {'access_token': self.integration.access_token}

        import requests

        resp = requests.post('https://slack.com/api/oauth.v2.access', data={
            'grant_type': 'refresh_token',
            'refresh_token': self.integration.refresh_token,
            'client_id': self.integration.config.get('client_id', ''),
            'client_secret': self.integration.config.get('client_secret', ''),
        }, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return {
            'access_token': data.get('access_token', self.integration.access_token),
            'refresh_token': data.get('refresh_token', self.integration.refresh_token),
            'expires_in': data.get('expires_in', 43200),
        }


# ---------------------------------------------------------------------------
# Service registry
# ---------------------------------------------------------------------------

SERVICE_REGISTRY = {
    'quickbooks': QuickBooksService,
    'xero': XeroService,
    'google_calendar': GoogleCalendarService,
    'outlook': OutlookCalendarService,
    'slack': SlackService,
}


def get_service(integration: Integration) -> BaseIntegrationService:
    """Factory: return the appropriate service for an integration."""
    cls = SERVICE_REGISTRY.get(integration.service_type)
    if not cls:
        raise ValueError(f"No service implementation for '{integration.service_type}'")
    return cls(integration)
