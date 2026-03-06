from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status as http_status
from apps.clients.models import Client
from .health_score import ClientHealthCalculator


class ClientHealthScoreView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id=None):
        if client_id:
            try:
                client = Client.objects.get(id=client_id)
            except Client.DoesNotExist:
                return Response({'error': 'Client not found'}, status=http_status.HTTP_404_NOT_FOUND)

            calculator = ClientHealthCalculator(client)
            score = calculator.calculate()
            score['client_id'] = str(client.id)
            score['client_name'] = client.company_name or f"{client.first_name} {client.last_name}"
            return Response(score)

        # Bulk: calculate for all active clients
        clients = Client.objects.filter(is_active=True)[:50]
        results = []
        for client in clients:
            calculator = ClientHealthCalculator(client)
            score = calculator.calculate()
            results.append({
                'client_id': str(client.id),
                'client_name': client.company_name or f"{client.first_name} {client.last_name}",
                'overall_score': score['overall_score'],
                'grade': score['grade'],
            })
        results.sort(key=lambda x: x['overall_score'], reverse=True)
        return Response({'clients': results, 'count': len(results)})
