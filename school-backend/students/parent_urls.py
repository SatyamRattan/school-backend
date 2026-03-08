from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .parent_views import ParentOverviewView, ParentAttendanceView, ParentBehaviorView, BehaviorReportViewSet

router = DefaultRouter()
router.register('behavior', BehaviorReportViewSet, basename='behavior-report')

urlpatterns = [
    path('overview/', ParentOverviewView.as_view(), name='parent-overview'),
    path('attendance/', ParentAttendanceView.as_view(), name='parent-attendance'),
    path('behavior-log/', ParentBehaviorView.as_view(), name='parent-behavior'),
    path('', include(router.urls)),
]
