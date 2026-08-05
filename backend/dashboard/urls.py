from django.urls import path
from dashboard.views import DashboardStatsAPIView, WeeklyGraphAPIView, GlobalSearchAPIView, HistoryAPIView

app_name = "dashboard"

urlpatterns = [
    path("stats/", DashboardStatsAPIView.as_view(), name="dashboard-stats"),
    path("weekly-graph/", WeeklyGraphAPIView.as_view(), name="weekly-graph"),
    path("search/", GlobalSearchAPIView.as_view(), name="global-search"),
    path("history/", HistoryAPIView.as_view(), name="history"),
]
