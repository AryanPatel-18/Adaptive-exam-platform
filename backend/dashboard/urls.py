from django.urls import path
from dashboard.views import DashboardStatsAPIView, WeeklyGraphAPIView

app_name = "dashboard"

urlpatterns = [
    path("stats/", DashboardStatsAPIView.as_view(), name="dashboard-stats"),
    path("weekly-graph/", WeeklyGraphAPIView.as_view(), name="weekly-graph"),
]
