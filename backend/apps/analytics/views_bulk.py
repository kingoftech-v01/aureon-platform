from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from apps.invoicing.models import Invoice
from apps.clients.models import Client


class BulkInvoiceActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        action = request.data.get('action')
        invoice_ids = request.data.get('invoice_ids', [])

        if not action or not invoice_ids:
            return Response({'error': 'action and invoice_ids required'}, status=status.HTTP_400_BAD_REQUEST)

        invoices = Invoice.objects.filter(id__in=invoice_ids)
        count = invoices.count()

        if action == 'send':
            updated = invoices.filter(status='draft').update(status='sent')
            return Response({'message': f'{updated} invoices sent', 'count': updated})

        elif action == 'mark_paid':
            from django.utils import timezone
            updated = invoices.filter(status__in=['sent', 'overdue']).update(
                status='paid', paid_at=timezone.now()
            )
            return Response({'message': f'{updated} invoices marked as paid', 'count': updated})

        elif action == 'cancel':
            updated = invoices.exclude(status='paid').update(status='cancelled')
            return Response({'message': f'{updated} invoices cancelled', 'count': updated})

        elif action == 'delete':
            deleted = invoices.filter(status='draft').delete()[0]
            return Response({'message': f'{deleted} draft invoices deleted', 'count': deleted})

        return Response({'error': f'Unknown action: {action}'}, status=status.HTTP_400_BAD_REQUEST)


class BulkClientActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        action = request.data.get('action')
        client_ids = request.data.get('client_ids', [])

        if not action or not client_ids:
            return Response({'error': 'action and client_ids required'}, status=status.HTTP_400_BAD_REQUEST)

        clients = Client.objects.filter(id__in=client_ids)

        if action == 'activate':
            updated = clients.update(lifecycle_stage='active')
            return Response({'message': f'{updated} clients activated', 'count': updated})

        elif action == 'deactivate':
            updated = clients.update(lifecycle_stage='inactive', is_active=False)
            return Response({'message': f'{updated} clients deactivated', 'count': updated})

        elif action == 'tag':
            tag = request.data.get('tag', '')
            if not tag:
                return Response({'error': 'tag required for tag action'}, status=status.HTTP_400_BAD_REQUEST)
            count = 0
            for client in clients:
                if client.tags is None:
                    client.tags = []
                if tag not in client.tags:
                    client.tags.append(tag)
                    client.save(update_fields=['tags'])
                    count += 1
            return Response({'message': f'{count} clients tagged', 'count': count})

        return Response({'error': f'Unknown action: {action}'}, status=status.HTTP_400_BAD_REQUEST)
