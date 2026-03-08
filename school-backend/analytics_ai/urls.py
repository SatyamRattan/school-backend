from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentRiskViewSet

router = DefaultRouter()
router.register(r'risks', StudentRiskViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
