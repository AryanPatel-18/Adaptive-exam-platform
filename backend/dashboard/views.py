from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from rest_framework.pagination import PageNumberPagination
from dashboard.services import DashboardService
from dashboard.serializers import DashboardStatsSerializer, UserActivitySerializer
from dashboard.models import UserActivity
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

class GlobalSearchAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "")
        if not query:
            return Response({"results": []})
            
        results = DashboardService.search_workspaces(request.user, query)
        return Response({"results": results})

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class HistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        activities = UserActivity.objects.filter(user=request.user).order_by('-timestamp')
        
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(activities, request)
        
        if page is not None:
            serializer = UserActivitySerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
            
        serializer = UserActivitySerializer(activities, many=True)
        return Response(serializer.data)
