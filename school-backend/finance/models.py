from django.db import models
from management.models import School
from students.models import Student
from core.choices import PaymentMethod, RazorpayOrderStatus, PaymentAuditType
import uuid

class FeeType(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='fee_types', null=True)
    name = models.CharField(max_length=100) # e.g., 'Tuition Fee', 'Transport Fee'
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('school', 'name')

class FeeStructure(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='fee_structures', null=True)
    fee_type = models.ForeignKey(FeeType, on_delete=models.CASCADE)
    classroom = models.ForeignKey('academics.Classroom', on_delete=models.CASCADE, null=True, blank=True)
    academic_year = models.CharField(max_length=20) # e.g., '2025-26'
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    # Late fine configuration
    late_fine_per_day = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    grace_period_days = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.fee_type.name} - {self.amount} ({self.academic_year})"

    class Meta:
        unique_together = ('school', 'fee_type', 'classroom', 'academic_year')

class FeePayment(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='fee_payments', null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student} - {self.amount_paid} on {self.payment_date}"


# ──────────────────────────────────────────────────────────────────────────────
# NEW: Razorpay Online Payment Layer
# ──────────────────────────────────────────────────────────────────────────────

class RazorpayOrder(models.Model):
    """
    Maps a Razorpay order to an internal fee payment intent.
    Serves as the idempotency anchor — one row per checkout attempt.
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='razorpay_orders', null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='razorpay_orders')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)

    # Idempotency: generated once per checkout session, checked on retry
    idempotency_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    razorpay_order_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=512, null=True, blank=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=10, choices=RazorpayOrderStatus.choices, default=RazorpayOrderStatus.CREATED)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    # Linked FeePayment created on successful verification
    fee_payment = models.OneToOneField(
        FeePayment, on_delete=models.SET_NULL, null=True, blank=True, related_name='razorpay_order'
    )

    class Meta:
        indexes = [
            models.Index(fields=['razorpay_order_id']),
            models.Index(fields=['student', 'status']),
        ]

    def __str__(self):
        return f"{self.razorpay_order_id} | {self.status}"


class PaymentAuditLog(models.Model):
    """
    Immutable, append-only audit trail.
    Records every state change in the payment lifecycle.
    Raw webhook payload is stored for forensic replay.
    """
    razorpay_order = models.ForeignKey(
        RazorpayOrder, on_delete=models.SET_NULL, null=True, related_name='audit_logs'
    )
    event_type = models.CharField(max_length=30, choices=PaymentAuditType.choices)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    payload_json = models.JSONField(null=True, blank=True)  # Raw webhook body
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Prevent modifications — audit logs are append-only
        if self.pk:
            raise ValueError("PaymentAuditLog entries are immutable and cannot be modified.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.event_type} at {self.created_at}"


class LateFine(models.Model):
    """
    Auto-generated late fines based on FeeStructure.late_fine_per_day.
    Admins can waive individual fines with a reason.
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='late_fines', null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='late_fines')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    days_overdue = models.IntegerField()
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_waived = models.BooleanField(default=False)
    waived_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='waived_fines'
    )
    waive_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'fee_structure')
        indexes = [models.Index(fields=['school', 'is_waived'])]

    def __str__(self):
        return f"Fine: {self.student} — ₹{self.fine_amount} ({'Waived' if self.is_waived else 'Active'})"


def upload_fee_receipt_pdf(instance, filename):
    school_code = instance.school.code if instance.school else 'default'
    return f'receipts/{school_code}/{instance.receipt_number}.pdf'

class FeeReceipt(models.Model):
    """
    Registry of all generated PDF receipts.
    Receipt numbers are sequential and school-scoped.
    """
    fee_payment = models.OneToOneField(FeePayment, on_delete=models.CASCADE, related_name='receipt')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='receipts', null=True)
    receipt_number = models.CharField(max_length=30, unique=True)  # e.g. RCP-2025-00042
    pdf_file = models.FileField(upload_to=upload_fee_receipt_pdf, null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.receipt_number
