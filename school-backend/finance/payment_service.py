"""
Payment service layer.
Handles Razorpay order creation, idempotency checks, and HMAC-SHA256 signature verification.
PCI compliance: no card data ever stored. Only IDs and signatures.
"""
import hmac
import hashlib
import razorpay
from decimal import Decimal
from django.conf import settings
from django.utils import timezone

from .models import RazorpayOrder, PaymentAuditLog, FeePayment
from core.choices import RazorpayOrderStatus, PaymentAuditType


def get_razorpay_client():
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


def initiate_payment(student, fee_structure, idempotency_key=None):
    """
    Creates a Razorpay order for the outstanding fee amount.
    If an idempotency_key is provided and an active order exists, return it (no double-charge).
    """
    from students.models import StudentAttendance

    # ── Idempotency Check ───────────────────────────────────────────
    if idempotency_key:
        existing = RazorpayOrder.objects.filter(
            idempotency_key=idempotency_key,
            status=RazorpayOrderStatus.CREATED
        ).first()
        if existing:
            return existing, False  # (order, was_created)

    # ── Calculate outstanding amount (partial payment support) ───────
    paid_total = sum(
        p.amount_paid for p in FeePayment.objects.filter(
            student=student, fee_structure=fee_structure
        )
    )
    outstanding = Decimal(fee_structure.amount) - paid_total
    if outstanding <= 0:
        raise ValueError("Fee already fully paid.")

    # ── Create Razorpay Order ─────────────────────────────────────────
    client = get_razorpay_client()
    rp_order = client.order.create({
        "amount": int(outstanding * 100),  # Razorpay takes paise
        "currency": "INR",
        "receipt": f"stu_{student.id}_fee_{fee_structure.id}",
        "payment_capture": 1,
    })

    order = RazorpayOrder.objects.create(
        school_id=student.school_id,
        student=student,
        fee_structure=fee_structure,
        razorpay_order_id=rp_order['id'],
        amount=outstanding,
        status=RazorpayOrderStatus.CREATED,
    )

    PaymentAuditLog.objects.create(
        razorpay_order=order,
        event_type=PaymentAuditType.INITIATED,
        payload_json={'razorpay_order_id': rp_order['id'], 'amount': str(outstanding)},
    )

    return order, True


def verify_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature, ip_address=None):
    """
    Verifies the HMAC-SHA256 signature from Razorpay.
    Returns (order, error_message) tuple.
    """
    try:
        order = RazorpayOrder.objects.get(razorpay_order_id=razorpay_order_id)
    except RazorpayOrder.DoesNotExist:
        return None, "Order not found."

    # Build expected signature
    body = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, razorpay_signature):
        PaymentAuditLog.objects.create(
            razorpay_order=order,
            event_type=PaymentAuditType.SIGNATURE_MISMATCH,
            razorpay_payment_id=razorpay_payment_id,
            ip_address=ip_address,
        )
        return order, "Signature verification failed."

    # Mark order as paid
    order.razorpay_payment_id = razorpay_payment_id
    order.razorpay_signature = razorpay_signature
    order.status = RazorpayOrderStatus.PAID
    order.paid_at = timezone.now()
    order.save()

    PaymentAuditLog.objects.create(
        razorpay_order=order,
        event_type=PaymentAuditType.VERIFIED,
        razorpay_payment_id=razorpay_payment_id,
        ip_address=ip_address,
    )

    # Create the actual FeePayment record
    payment = FeePayment.objects.create(
        school_id=order.school_id,
        student=order.student,
        fee_structure=order.fee_structure,
        amount_paid=order.amount,
        payment_method='ONLINE',
        transaction_id=razorpay_payment_id,
        remarks=f"Razorpay Order: {razorpay_order_id}",
    )
    order.fee_payment = payment
    order.save()

    PaymentAuditLog.objects.create(
        razorpay_order=order,
        event_type=PaymentAuditType.PAYMENT_CREATED,
        razorpay_payment_id=razorpay_payment_id,
    )

    return order, None


def calculate_late_fine(student, fee_structure):
    """
    Calculates and upserts a LateFine record if payment is past due date.
    Returns fine amount (or 0 if not overdue).
    """
    from django.utils import timezone
    from datetime import date

    today = date.today()
    due = fee_structure.due_date
    grace = fee_structure.grace_period_days
    rate = fee_structure.late_fine_per_day

    if today <= due or rate == 0:
        return Decimal('0')

    days_overdue = max(0, (today - due).days - grace)
    if days_overdue == 0:
        return Decimal('0')

    fine_amount = Decimal(str(days_overdue)) * rate

    LateFine.objects.update_or_create(
        student=student,
        fee_structure=fee_structure,
        defaults={
            'school_id': student.school_id,
            'days_overdue': days_overdue,
            'fine_amount': fine_amount,
        }
    )
    return fine_amount
