"""
Contracts Celery tasks for Aureon SaaS Platform.

These tasks handle contract generation and expiration checks.
"""
from celery import shared_task
from django.utils import timezone
from django.core.files.base import ContentFile
import logging
import io

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def generate_contract_pdf(self, contract_id):
    """Generate PDF for a contract."""
    try:
        from apps.contracts.models import Contract
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors

        contract = Contract.objects.select_related('client', 'owner').get(id=contract_id)
        logger.info(f"Generating PDF for contract {contract.contract_number}...")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                topMargin=0.75*inch, bottomMargin=0.75*inch)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        elements.append(Paragraph(f"Contract: {contract.title}", styles['Title']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Contract #: {contract.contract_number}", styles['Normal']))
        elements.append(Paragraph(f"Status: {contract.get_status_display()}", styles['Normal']))
        elements.append(Spacer(1, 12))

        # Client info
        elements.append(Paragraph("Client Information", styles['Heading2']))
        elements.append(Paragraph(f"Client: {contract.client}", styles['Normal']))
        elements.append(Spacer(1, 12))

        # Contract details
        elements.append(Paragraph("Contract Details", styles['Heading2']))
        details = [
            ['Type', contract.get_contract_type_display()],
            ['Start Date', str(contract.start_date)],
            ['End Date', str(contract.end_date) if contract.end_date else 'Ongoing'],
            ['Value', f"{contract.currency} {contract.value:,.2f}"],
        ]
        t = Table(details, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.9, 0.9, 0.9)),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))

        # Description
        if contract.description:
            elements.append(Paragraph("Scope of Work", styles['Heading2']))
            elements.append(Paragraph(contract.description, styles['Normal']))
            elements.append(Spacer(1, 12))

        # Terms
        if contract.terms_and_conditions:
            elements.append(Paragraph("Terms and Conditions", styles['Heading2']))
            elements.append(Paragraph(contract.terms_and_conditions, styles['Normal']))
            elements.append(Spacer(1, 12))

        # Payment terms
        if contract.payment_terms:
            elements.append(Paragraph("Payment Terms", styles['Heading2']))
            elements.append(Paragraph(contract.payment_terms, styles['Normal']))

        # Signature block
        elements.append(Spacer(1, 36))
        elements.append(Paragraph("Signatures", styles['Heading2']))
        sig_data = [
            ['Company Representative', 'Client'],
            [
                'Signed' if contract.signed_by_company else '________________________',
                'Signed' if contract.signed_by_client else '________________________',
            ],
            [
                f"Date: {contract.signed_at.strftime('%Y-%m-%d') if contract.signed_at else '___________'}",
                f"Date: {contract.signed_at.strftime('%Y-%m-%d') if contract.signed_at else '___________'}",
            ],
        ]
        sig_table = Table(sig_data, colWidths=[3*inch, 3*inch])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(sig_table)

        doc.build(elements)

        # Save PDF to contract
        pdf_content = buffer.getvalue()
        buffer.close()
        filename = f"{contract.contract_number}.pdf"
        contract.contract_file.save(filename, ContentFile(pdf_content), save=True)

        logger.info(f"PDF generated for contract {contract.contract_number}")
        return {'status': 'success', 'contract_id': str(contract_id), 'filename': filename}
    except Exception as exc:
        logger.error(f"Contract PDF generation failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=2)
def send_contract_for_signature(self, contract_id):
    """Send contract for e-signature via email."""
    try:
        from apps.contracts.models import Contract
        from apps.notifications.services import NotificationService

        contract = Contract.objects.select_related('client').get(id=contract_id)
        logger.info(f"Sending contract {contract.contract_number} for signature...")

        # Generate PDF if not already generated
        if not contract.contract_file:
            generate_contract_pdf(contract_id)
            contract.refresh_from_db()

        # Update status to pending signature
        if contract.status == Contract.DRAFT:
            contract.status = Contract.PENDING
            contract.save(update_fields=['status', 'updated_at'])

        # Send notification to client
        try:
            NotificationService.send_contract_notification(
                contract, 'contract_signature_request'
            )
        except Exception as e:
            logger.warning(f"Could not send signature notification: {e}")

        logger.info(f"Contract {contract.contract_number} sent for signature")
        return {'status': 'success', 'contract_id': str(contract_id)}
    except Exception as exc:
        logger.error(f"Contract send failed: {exc}")
        raise self.retry(exc=exc, countdown=120)


@shared_task(bind=True, max_retries=2)
def check_contract_expirations(self):
    """Check for expiring contracts and send notifications. Runs daily at 8 AM."""
    try:
        from apps.contracts.models import Contract
        from apps.notifications.services import NotificationService

        logger.info("Checking contract expirations...")

        # Find contracts expiring in the next 30 days
        today = timezone.now().date()
        thirty_days = today + timezone.timedelta(days=30)

        expiring_contracts = Contract.objects.filter(
            status=Contract.ACTIVE,
            end_date__gte=today,
            end_date__lte=thirty_days
        ).select_related('client', 'owner')

        notified_count = 0
        for contract in expiring_contracts:
            days_until_expiry = (contract.end_date - today).days
            try:
                NotificationService.send_contract_notification(
                    contract, 'contract_expiring'
                )
                notified_count += 1
                logger.info(
                    f"Contract {contract.contract_number} expires in {days_until_expiry} days - notification sent"
                )
            except Exception as e:
                logger.warning(f"Could not send expiration notification for {contract.contract_number}: {e}")

        # Find already expired contracts and update status
        expired_contracts = Contract.objects.filter(
            status=Contract.ACTIVE,
            end_date__lt=today
        )
        expired_count = expired_contracts.update(status=Contract.COMPLETED)

        logger.info(f"Contract expiration check: {notified_count} expiring, {expired_count} expired")
        return {
            'status': 'success',
            'timestamp': timezone.now().isoformat(),
            'expiring_notified': notified_count,
            'expired_updated': expired_count
        }
    except Exception as exc:
        logger.error(f"Contract expiration check failed: {exc}")
        raise self.retry(exc=exc, countdown=300)
