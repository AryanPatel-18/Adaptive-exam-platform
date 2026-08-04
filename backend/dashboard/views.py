from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from dashboard.services import DashboardService
from dashboard.serializers import DashboardStatsSerializer
import logging

logger = logging.getLogger(__name__)

class DashboardStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logger.info("Fetching dashboard stats for user: %s", request.user.id)
        stats = DashboardService.get_user_dashboard_stats(request.user)
        serializer = DashboardStatsSerializer(stats, context={'request': request})
        return Response(serializer.data)

class WeeklyGraphAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        image_bytes = DashboardService.generate_weekly_graph(request.user)
        return HttpResponse(image_bytes, content_type="image/png")
