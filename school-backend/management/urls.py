from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SchoolViewSet, CustomDomainViewSet, 
    SubscriptionViewSet, TenantDatabaseViewSet, PaymentViewSet
)

router = DefaultRouter()
router.register(r'schools', SchoolViewSet)
router.register(r'domains', CustomDomainViewSet)
router.register(r'subscriptions', SubscriptionViewSet)
router.register(r'databases', TenantDatabaseViewSet)
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
]
