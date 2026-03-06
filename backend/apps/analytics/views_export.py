import csv
import io
from datetime import datetime
from django.http import HttpResponse
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from apps.invoicing.models import Invoice
from apps.payments.models import Payment
from apps.clients.models import Client
from apps.contracts.models import Contract


class ExportReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        report_type = request.query_params.get('report_type', 'comprehensive')
        format_type = request.query_params.get('format', 'csv')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if format_type == 'csv':
            return self._export_csv(report_type, start_date, end_date)
        else:
            return HttpResponse('PDF export coming soon', status=501)

    def _export_csv(self, report_type, start_date, end_date):
        output = io.StringIO()
        writer = csv.writer(output)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if report_type == 'invoices':
            writer.writerow(['Invoice #', 'Client', 'Status', 'Issue Date', 'Due Date', 'Subtotal', 'Tax', 'Total', 'Paid'])
            qs = Invoice.objects.select_related('client').all().order_by('-created_at')
            if start_date:
                qs = qs.filter(issue_date__gte=start_date)
            if end_date:
                qs = qs.filter(issue_date__lte=end_date)
            for inv in qs:
                client_name = inv.client.company_name or f"{inv.client.first_name} {inv.client.last_name}"
                writer.writerow([inv.invoice_number, client_name, inv.status, inv.issue_date, inv.due_date, inv.subtotal, inv.tax_amount, inv.total, inv.paid_amount])

        elif report_type == 'payments':
            writer.writerow(['Transaction ID', 'Invoice #', 'Client', 'Amount', 'Status', 'Method', 'Date'])
            qs = Payment.objects.select_related('invoice', 'invoice__client').all().order_by('-created_at')
            if start_date:
                qs = qs.filter(payment_date__gte=start_date)
            if end_date:
                qs = qs.filter(payment_date__lte=end_date)
            for pay in qs:
                client_name = ''
                invoice_num = ''
                if pay.invoice:
                    invoice_num = pay.invoice.invoice_number
                    if pay.invoice.client:
                        client_name = pay.invoice.client.company_name or f"{pay.invoice.client.first_name} {pay.invoice.client.last_name}"
                writer.writerow([pay.transaction_id, invoice_num, client_name, pay.amount, pay.status, pay.payment_method, pay.payment_date])

        elif report_type == 'clients':
            writer.writerow(['Name', 'Email', 'Type', 'Stage', 'Total Value', 'Outstanding', 'Created'])
            qs = Client.objects.all().order_by('-created_at')
            for client in qs:
                name = client.company_name or f"{client.first_name} {client.last_name}"
                writer.writerow([name, client.email, client.client_type, client.lifecycle_stage, client.total_value, client.outstanding_balance, client.created_at.date()])

        elif report_type == 'comprehensive':
            writer.writerow(['=== AUREON FINANCE REPORT ==='])
            writer.writerow([f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}'])
            writer.writerow([])

            writer.writerow(['--- SUMMARY ---'])
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total Clients', Client.objects.count()])
            writer.writerow(['Active Contracts', Contract.objects.filter(status='active').count()])
            writer.writerow(['Total Invoices', Invoice.objects.count()])
            writer.writerow(['Total Revenue', float(Payment.objects.filter(status='succeeded').aggregate(t=Sum('amount'))['t'] or 0)])
            writer.writerow([])

            writer.writerow(['--- INVOICES ---'])
            writer.writerow(['Invoice #', 'Client', 'Status', 'Total'])
            for inv in Invoice.objects.select_related('client').order_by('-created_at')[:50]:
                client_name = inv.client.company_name or f"{inv.client.first_name} {inv.client.last_name}" if inv.client else 'N/A'
                writer.writerow([inv.invoice_number, client_name, inv.status, inv.total])

        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="aureon_{report_type}_{timestamp}.csv"'
        return response
