from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .ai_insights import InsightsEngine


class AIInsightsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        engine = InsightsEngine(user=request.user)
        insights = engine.generate_all_insights()
        return Response({
            'insights': insights,
            'generated_at': engine.now.isoformat(),
            'count': len(insights),
        })
