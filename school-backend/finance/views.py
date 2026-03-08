"""
Finance views — extends existing views with Razorpay payment flow,
webhook handling, revenue analytics, and receipt management.
All existing endpoints are preserved unchanged.
"""
import json
import hmac
import hashlib
from decimal import Decimal

from django.conf import settings
from django.db.models import Sum, Count, Q, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncMonth
from django.http import FileResponse
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FeeType, FeeStructure, FeePayment, RazorpayOrder, LateFine, FeeReceipt
from .serializers import (
    FeeTypeSerializer, FeeStructureSerializer, FeePaymentSerializer,
    RazorpayOrderSerializer, LateFineSerializer, FeeReceiptSerializer
)
from .payment_service import initiate_payment, verify_payment, calculate_late_fine
from core.permissions import IsFinanceStaff, IsStudentOrParent


# ─────────────────────────────────────────────────────────────────────────────
# Existing ViewSets (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

class FeeTypeViewSet(viewsets.ModelViewSet):
    serializer_class = FeeTypeSerializer
    permission_classes = [permissions.IsAuthenticated, IsFinanceStaff]
    search_fields = ['name']
    filterset_fields = ['school_id']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return FeeType.objects.all()
        if hasattr(user, 'school_id') and user.school_id:
            return FeeType.objects.filter(school_id=user.school_id)
        return FeeType.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'school_id') and user.school_id:
            serializer.save(school_id=user.school_id)
        else:
            serializer.save()


class FeeStructureViewSet(viewsets.ModelViewSet):
    serializer_class = FeeStructureSerializer
    permission_classes = [permissions.IsAuthenticated, IsFinanceStaff]
    filterset_fields = ['classroom', 'school_id']
    search_fields = ['fee_type__name']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return FeeStructure.objects.select_related('fee_type', 'classroom').all()
        if hasattr(user, 'school_id') and user.school_id:
            return FeeStructure.objects.select_related('fee_type', 'classroom').filter(school_id=user.school_id)
        return FeeStructure.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'school_id') and user.school_id:
            serializer.save(school_id=user.school_id)
        else:
            serializer.save()


class FeePaymentViewSet(viewsets.ModelViewSet):
    serializer_class = FeePaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsFinanceStaff | IsStudentOrParent]
    filterset_fields = ['school_id']
    search_fields = ['student__first_name', 'student__last_name', 'student__admission_number']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return FeePayment.objects.select_related('student', 'fee_structure__fee_type').all()

        base_qs = FeePayment.objects.select_related('student', 'fee_structure__fee_type')

        if user.role in ['SCHOOL_ADMIN', 'ACCOUNTANT']:
            if hasattr(user, 'school_id') and user.school_id:
                return base_qs.filter(school_id=user.school_id)
            return base_qs

        if user.role == 'STUDENT':
            return base_qs.filter(student__user=user)

        if user.role == 'PARENT':
            return base_qs.filter(student__parent__user=user)

        return FeePayment.objects.none()

    @action(detail=False, methods=['get'])
    def my_dues(self, request):
        """Returns outstanding dues with late fine calculation."""
        from students.models import Student
        user = request.user
        student = None

        if user.role == 'STUDENT':
            student = Student.objects.filter(user=user).first()
        elif user.role == 'PARENT':
            student_id = request.query_params.get('student_id')
            if student_id:
                student = Student.objects.filter(id=student_id, parent__user=user).first()
            else:
                student = Student.objects.filter(parent__user=user).first()

        if not student:
            return Response({"error": "No student associated with this account."}, status=400)
        if not student.classroom:
            return Response({"error": "Student is not assigned to any classroom."}, status=400)

        structures = FeeStructure.objects.filter(
            classroom=student.classroom,
            school_id=student.school_id
        ).select_related('fee_type')

        payments = FeePayment.objects.filter(student=student)

        dues = []
        for struct in structures:
            paid_amount = sum(p.amount_paid for p in payments if p.fee_structure_id == struct.id)
            if paid_amount < struct.amount:
                fine = calculate_late_fine(student, struct)
                dues.append({
                    "id": struct.id,
                    "fee_type_name": struct.fee_type.name,
                    "total_amount": struct.amount,
                    "paid_amount": paid_amount,
                    "due_amount": struct.amount - paid_amount,
                    "late_fine": fine,
                    "total_payable": (struct.amount - paid_amount) + fine,
                    "due_date": struct.due_date,
                    "academic_year": struct.academic_year,
                })

        return Response(dues)

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'school_id') and user.school_id:
            payment = serializer.save(school_id=user.school_id)
        else:
            payment = serializer.save()

        from notifications.services import send_notification
        from .tasks import generate_and_send_receipt

        if hasattr(payment.student, 'user') and payment.student.user:
            send_notification(
                payment.student.user,
                "Payment Received",
                f"We received a payment of {payment.amount_paid} for {payment.fee_structure.fee_type.name}.",
                notification_type='FEE_DUE',
                channels=['in_app', 'email']
            )

        if (hasattr(payment.student, 'parent') and payment.student.parent
                and hasattr(payment.student.parent, 'user') and payment.student.parent.user):
            send_notification(
                payment.student.parent.user,
                "Fee Payment Confirmation",
                f"Payment of {payment.amount_paid} received for {payment.student.first_name}.",
                notification_type='FEE_DUE',
                channels=['in_app', 'email']
            )

        generate_and_send_receipt.delay(payment.id)


# ─────────────────────────────────────────────────────────────────────────────
# NEW: Razorpay Payment Flow
# ─────────────────────────────────────────────────────────────────────────────

class InitiatePaymentView(APIView):
    """
    POST /api/finance/payments/initiate/
    Creates a Razorpay order. Idempotency enforced via idempotency_key.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from students.models import Student
        fee_structure_id = request.data.get('fee_structure_id')
        idempotency_key = request.data.get('idempotency_key')

        if not fee_structure_id:
            return Response({'error': 'fee_structure_id required.'}, status=400)

        # Students/parents can only pay for their own fee
        user = request.user
        student = None
        if user.role == 'STUDENT':
            student = Student.objects.filter(user=user).first()
        elif user.role == 'PARENT':
            student_id = request.data.get('student_id')
            student = Student.objects.filter(id=student_id, parent__user=user).first()

        if not student:
            return Response({'error': 'Student not found.'}, status=404)

        try:
            fee_structure = FeeStructure.objects.get(pk=fee_structure_id, school_id=user.school_id)
        except FeeStructure.DoesNotExist:
            return Response({'error': 'Fee structure not found.'}, status=404)

        try:
            order, created = initiate_payment(student, fee_structure, idempotency_key)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        return Response({
            'razorpay_order_id': order.razorpay_order_id,
            'amount': int(order.amount * 100),
            'currency': order.currency,
            'key_id': settings.RAZORPAY_KEY_ID,
            'idempotency_key': str(order.idempotency_key),
            'was_created': created,
        })


class VerifyPaymentView(APIView):
    """
    POST /api/finance/payments/verify/
    Verifies the HMAC-SHA256 signature returned by Razorpay checkout.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from .tasks import generate_and_send_receipt
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response({'error': 'razorpay_order_id, razorpay_payment_id, razorpay_signature required.'}, status=400)

        ip = request.META.get('REMOTE_ADDR')
        order, error = verify_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature, ip)

        if error:
            return Response({'error': error}, status=400)

        # Trigger async receipt generation
        if order.fee_payment_id:
            generate_and_send_receipt.delay(order.fee_payment_id)

        return Response({
            'status': 'PAID',
            'payment_id': razorpay_payment_id,
            'message': 'Payment verified. Receipt will be emailed shortly.',
        })


class RazorpayWebhookView(APIView):
    """
    POST /api/finance/webhook/razorpay/
    Server-side webhook handler. Validates X-Razorpay-Signature header.
    Processes events asynchronously via Celery.
    """
    permission_classes = []  # Public endpoint — secured via HMAC
    authentication_classes = []

    def post(self, request):
        from .tasks import process_webhook_event
        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET

        # Verify signature
        signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE', '')
        body = request.body

        expected = hmac.new(
            webhook_secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected, signature):
            return Response({'error': 'Invalid signature.'}, status=400)

        payload = json.loads(body)
        event = payload.get('event', '')

        if event == 'payment.captured':
            payment_entity = payload['payload']['payment']['entity']
            order_id = payment_entity.get('order_id')
            payment_id = payment_entity.get('id')
            # Dispatch async — prevents Razorpay timeout retries
            process_webhook_event.delay(order_id, payment_id, payload)

        return Response({'status': 'ok'})


# ─────────────────────────────────────────────────────────────────────────────
# Revenue Analytics
# ─────────────────────────────────────────────────────────────────────────────

class RevenueAnalyticsView(APIView):
    """
    GET /api/finance/revenue/analytics/
    Returns financial aggregations for the admin finance dashboard.
    """
    permission_classes = [permissions.IsAuthenticated, IsFinanceStaff]

    def get(self, request):
        school_id = request.user.school_id
        qs = FeePayment.objects.filter(school_id=school_id)

        # Monthly revenue
        monthly = (
            qs.annotate(month=TruncMonth('payment_date'))
            .values('month')
            .annotate(total=Sum('amount_paid'))
            .order_by('month')
        )

        # Revenue by fee type
        by_type = (
            qs.values('fee_structure__fee_type__name')
            .annotate(total=Sum('amount_paid'), count=Count('id'))
            .order_by('-total')
        )

        # Total collected vs total due
        total_collected = qs.aggregate(total=Sum('amount_paid'))['total'] or 0
        total_due = FeeStructure.objects.filter(school_id=school_id).aggregate(
            total=Sum('amount'))['total'] or 0
        collection_rate = round((float(total_collected) / float(total_due)) * 100, 1) if total_due else 0

        # Outstanding late fines
        active_fines = LateFine.objects.filter(school_id=school_id, is_waived=False).aggregate(
            total=Sum('fine_amount'), count=Count('id')
        )

        # Top 5 defaulters
        from students.models import Student
        defaulters = []
        students = Student.objects.filter(school_id=school_id)
        for student in students:
            paid = FeePayment.objects.filter(student=student).aggregate(p=Sum('amount_paid'))['p'] or 0
            due_total = FeeStructure.objects.filter(
                classroom=student.classroom, school_id=school_id
            ).aggregate(d=Sum('amount'))['d'] or 0
            outstanding = float(due_total) - float(paid)
            if outstanding > 0:
                defaulters.append({
                    'student': str(student),
                    'admission_number': student.admission_number,
                    'outstanding': outstanding
                })
        defaulters.sort(key=lambda x: x['outstanding'], reverse=True)

        return Response({
            'summary': {
                'total_collected': total_collected,
                'total_due': total_due,
                'collection_rate': collection_rate,
            },
            'monthly_revenue': [
                {'month': m['month'].strftime('%b %Y'), 'total': m['total']} for m in monthly
            ],
            'by_fee_type': list(by_type),
            'active_fines': active_fines,
            'top_defaulters': defaulters[:5],
        })


class LateFineViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LateFineSerializer
    permission_classes = [permissions.IsAuthenticated, IsFinanceStaff]

    def get_queryset(self):
        return LateFine.objects.filter(
            school_id=self.request.user.school_id
        ).select_related('student', 'fee_structure__fee_type')

    @action(detail=True, methods=['post'])
    def waive(self, request, pk=None):
        fine = self.get_object()
        fine.is_waived = True
        fine.waived_by = request.user
        fine.waive_reason = request.data.get('reason', '')
        fine.save()
        return Response({'status': 'Fine waived.'})


class FeeReceiptViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FeeReceiptSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['school_id']

    def get_queryset(self):
        user = self.request.user
        if user.role in ['SCHOOL_ADMIN', 'ACCOUNTANT'] or user.is_superuser:
            return FeeReceipt.objects.filter(school_id=user.school_id).select_related('fee_payment')
        if user.role == 'STUDENT':
            return FeeReceipt.objects.filter(fee_payment__student__user=user)
        if user.role == 'PARENT':
            return FeeReceipt.objects.filter(fee_payment__student__parent__user=user)
        return FeeReceipt.objects.none()

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        receipt = self.get_object()
        if receipt.pdf_file:
            return FileResponse(receipt.pdf_file.open(), content_type='application/pdf')
        return Response({'error': 'PDF not yet generated.'}, status=404)
