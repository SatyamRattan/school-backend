from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FeeTypeViewSet, FeeStructureViewSet, FeePaymentViewSet,
    LateFineViewSet, FeeReceiptViewSet,
    InitiatePaymentView, VerifyPaymentView,
    RazorpayWebhookView, RevenueAnalyticsView
)

router = DefaultRouter()
router.register(r'fee-types', FeeTypeViewSet, basename='feetype')
router.register(r'fee-structures', FeeStructureViewSet, basename='feestructure')
router.register(r'payments', FeePaymentViewSet, basename='feepayment')
router.register(r'fines', LateFineViewSet, basename='latefine')
router.register(r'receipts', FeeReceiptViewSet, basename='feereceipt')

urlpatterns = [
    path('', include(router.urls)),
    # Payment flow
    path('payments/initiate/', InitiatePaymentView.as_view(), name='payment-initiate'),
    path('payments/verify/', VerifyPaymentView.as_view(), name='payment-verify'),
    # Webhook — public, secured via HMAC
    path('webhook/razorpay/', RazorpayWebhookView.as_view(), name='razorpay-webhook'),
    # Analytics
    path('revenue/analytics/', RevenueAnalyticsView.as_view(), name='revenue-analytics'),
]
