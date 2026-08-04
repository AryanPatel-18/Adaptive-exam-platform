from django.contrib import admin
from django.urls import path,include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/',include("authentication.urls")),
    path('api/workspace/',include("workspace.urls")),
    path('api/files/',include("files.urls")),
    path('api/processing/',include("processing.urls")),
    path('api/quiz/',include("quiz.urls")),
    path('api/schedule/',include("schedule.urls")),
    path('api/dashboard/',include("dashboard.urls")),
]
