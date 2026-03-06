"""
Invoicing Celery tasks for Aureon SaaS Platform.

These tasks handle invoice generation and payment reminders.
"""
from celery import shared_task
from django.utils import timezone
from django.core.files.base import ContentFile
import logging
import io

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_invoice(self, invoice_id):
    """Generate a formatted PDF for an invoice."""
    try:
        from apps.invoicing.models import Invoice
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors

        invoice = Invoice.objects.select_related('client', 'contract').prefetch_related('items').get(id=invoice_id)
        logger.info(f"Generating PDF for invoice {invoice.invoice_number}...")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                topMargin=0.75*inch, bottomMargin=0.75*inch)
        styles = getSampleStyleSheet()
        elements = []

        # Header
        elements.append(Paragraph(f"INVOICE", styles['Title']))
        elements.append(Paragraph(f"#{invoice.invoice_number}", styles['Heading2']))
        elements.append(Spacer(1, 12))

        # Invoice info
        info_data = [
            ['Issue Date:', str(invoice.issue_date), 'Due Date:', str(invoice.due_date)],
            ['Status:', invoice.get_status_display(), 'Currency:', invoice.currency],
        ]
        info_table = Table(info_data, colWidths=[1.2*inch, 2*inch, 1.2*inch, 2*inch])
        info_table.setStyle(TableStyle([
            ('PADDING', (0, 0), (-1, -1), 4),
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONT', (2, 0), (2, -1), 'Helvetica-Bold'),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 12))

        # Client info
        elements.append(Paragraph("Bill To:", styles['Heading3']))
        elements.append(Paragraph(str(invoice.client), styles['Normal']))
        elements.append(Spacer(1, 12))

        # Line items
        elements.append(Paragraph("Line Items", styles['Heading3']))
        item_data = [['Description', 'Qty', 'Unit Price', 'Amount']]
        for item in invoice.items.all():
            item_data.append([
                item.description,
                f"{item.quantity:.2f}",
                f"${item.unit_price:,.2f}",
                f"${item.amount:,.2f}"
            ])
        item_table = Table(item_data, colWidths=[3*inch, 1*inch, 1.25*inch, 1.25*inch])
        item_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.2, 0.2)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(item_table)
        elements.append(Spacer(1, 12))

        # Totals
        totals_data = [
            ['Subtotal:', f"${invoice.subtotal:,.2f}"],
            [f'Tax ({invoice.tax_rate}%):', f"${invoice.tax_amount:,.2f}"],
        ]
        if invoice.discount_amount > 0:
            totals_data.append(['Discount:', f"-${invoice.discount_amount:,.2f}"])
        totals_data.append(['TOTAL:', f"${invoice.total:,.2f}"])
        if invoice.paid_amount > 0:
            totals_data.append(['Paid:', f"${invoice.paid_amount:,.2f}"])
            totals_data.append(['Balance Due:', f"${invoice.balance_due:,.2f}"])

        totals_table = Table(totals_data, colWidths=[4.5*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONT', (-2, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(totals_table)

        # Notes
        if invoice.notes:
            elements.append(Spacer(1, 24))
            elements.append(Paragraph("Notes:", styles['Heading3']))
            elements.append(Paragraph(invoice.notes, styles['Normal']))

        # Terms
        if invoice.terms:
            elements.append(Spacer(1, 12))
            elements.append(Paragraph("Terms:", styles['Heading3']))
            elements.append(Paragraph(invoice.terms, styles['Normal']))

        doc.build(elements)

        pdf_content = buffer.getvalue()
        buffer.close()
        filename = f"{invoice.invoice_number}.pdf"
        invoice.pdf_file.save(filename, ContentFile(pdf_content), save=True)

        logger.info(f"PDF generated for invoice {invoice.invoice_number}")
        return {'status': 'success', 'invoice_id': str(invoice_id), 'filename': filename}
    except Exception as exc:
        logger.error(f"Invoice PDF generation failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_invoice_email(self, invoice_id):
    """Send invoice email to client."""
    try:
        from apps.invoicing.models import Invoice
        from apps.notifications.services import NotificationService

        invoice = Invoice.objects.select_related('client').get(id=invoice_id)
        logger.info(f"Sending invoice email for {invoice.invoice_number}...")

        # Generate PDF if not exists
        if not invoice.pdf_file:
            generate_invoice(invoice_id)
            invoice.refresh_from_db()

        # Send notification
        NotificationService.send_invoice_notification(invoice, 'invoice_sent')

        # Mark as sent
        invoice.mark_as_sent()

        logger.info(f"Invoice email sent for {invoice.invoice_number}")
        return {'status': 'success', 'invoice_id': str(invoice_id)}
    except Exception as exc:
        logger.error(f"Invoice email failed: {exc}")
        raise self.retry(exc=exc, countdown=120)


@shared_task(bind=True, max_retries=2)
def generate_recurring_invoices(self):
    """Generate recurring invoices. Runs daily at midnight."""
    try:
        from apps.contracts.models import Contract
        from apps.invoicing.models import Invoice

        logger.info("Generating recurring invoices...")
        today = timezone.now().date()
        generated_count = 0

        # Find active retainer/recurring contracts that need invoicing
        active_contracts = Contract.objects.filter(
            status=Contract.ACTIVE,
            contract_type__in=[Contract.RETAINER, Contract.MILESTONE],
            invoice_schedule__isnull=False,
        ).exclude(invoice_schedule='').select_related('client')

        for contract in active_contracts:
            # Check if invoice already exists for this period
            last_invoice = Invoice.objects.filter(
                contract=contract,
            ).order_by('-issue_date').first()

            # Determine if a new invoice is due
            should_generate = False
            if not last_invoice:
                should_generate = True
            elif contract.invoice_schedule.lower() == 'monthly':
                next_date = last_invoice.issue_date.replace(day=1)
                if last_invoice.issue_date.month == 12:
                    next_date = next_date.replace(year=next_date.year + 1, month=1)
                else:
                    next_date = next_date.replace(month=next_date.month + 1)
                should_generate = today >= next_date
            elif contract.invoice_schedule.lower() == 'weekly':
                should_generate = (today - last_invoice.issue_date).days >= 7

            if should_generate:
                # Create invoice
                due_date = today + timezone.timedelta(days=30)
                invoice = Invoice.objects.create(
                    client=contract.client,
                    contract=contract,
                    status=Invoice.DRAFT,
                    issue_date=today,
                    due_date=due_date,
                    subtotal=contract.value,
                    total=contract.value,
                    currency=contract.currency,
                    notes=f"Recurring invoice for contract {contract.contract_number}",
                )
                generated_count += 1
                logger.info(f"Generated recurring invoice {invoice.invoice_number} for contract {contract.contract_number}")

        logger.info(f"Generated {generated_count} recurring invoices")
        return {
            'status': 'success',
            'date': today.isoformat(),
            'invoices_generated': generated_count
        }
    except Exception as exc:
        logger.error(f"Recurring invoice generation failed: {exc}")
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=2)
def send_payment_reminders(self):
    """Send payment reminders for overdue invoices. Runs daily at 9 AM."""
    try:
        from apps.invoicing.models import Invoice
        from apps.notifications.services import NotificationService

        logger.info("Sending payment reminders...")
        today = timezone.now().date()

        # Find overdue invoices
        overdue_invoices = Invoice.objects.filter(
            status__in=[Invoice.SENT, Invoice.VIEWED, Invoice.PARTIALLY_PAID],
            due_date__lt=today,
        ).select_related('client')

        sent_count = 0
        for invoice in overdue_invoices:
            # Update status to overdue
            if invoice.status != Invoice.OVERDUE:
                invoice.status = Invoice.OVERDUE
                invoice.save(update_fields=['status', 'updated_at'])

            days_overdue = (today - invoice.due_date).days
            try:
                NotificationService.send_invoice_notification(invoice, 'payment_reminder')
                sent_count += 1
                logger.info(f"Payment reminder sent for {invoice.invoice_number} ({days_overdue} days overdue)")
            except Exception as e:
                logger.warning(f"Could not send reminder for {invoice.invoice_number}: {e}")

        logger.info(f"Sent {sent_count} payment reminders")
        return {
            'status': 'success',
            'timestamp': timezone.now().isoformat(),
            'reminders_sent': sent_count
        }
    except Exception as exc:
        logger.error(f"Payment reminders failed: {exc}")
        raise self.retry(exc=exc, countdown=300)
