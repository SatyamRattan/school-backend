"""
Celery tasks for the finance app:
- generate_and_send_receipt: Creates a PDF receipt and emails it to parent/student
- process_webhook_event: Async processing of Razorpay webhook events
"""
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.core.mail import EmailMessage
import io
import logging

logger = logging.getLogger(__name__)


def _generate_receipt_number(school_id):
    """Generate sequential receipt numbers: RCP-YYYY-SCHOOLID-NNNNN"""
    from .models import FeeReceipt
    from django.utils import timezone
    year = timezone.now().year
    count = FeeReceipt.objects.filter(school_id=school_id).count() + 1
    return f"RCP-{year}-{school_id}-{count:05d}"


def _build_receipt_pdf(payment):
    """Build a simple but professional PDF receipt using reportlab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
    except ImportError:
        logger.warning("reportlab not installed — skipping PDF generation.")
        return None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"<b>{settings.SCHOOL_NAME}</b>", styles['Title']))
    elements.append(Paragraph("Fee Payment Receipt", styles['h2']))
    elements.append(Spacer(1, 10*mm))

    data = [
        ['Receipt No', getattr(payment, 'receipt', None) and payment.receipt.receipt_number or 'N/A'],
        ['Date', payment.payment_date.strftime('%d %b %Y')],
        ['Student', str(payment.student)],
        ['Admission No', payment.student.admission_number],
        ['Fee Type', payment.fee_structure.fee_type.name],
        ['Academic Year', payment.fee_structure.academic_year],
        ['Amount Paid', f"₹ {payment.amount_paid}"],
        ['Payment Method', payment.get_payment_method_display()],
        ['Transaction ID', payment.transaction_id or '—'],
    ]

    table = Table(data, colWidths=[60*mm, 100*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightyellow),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def generate_and_send_receipt(self, fee_payment_id):
    """
    Generates a PDF receipt for a FeePayment and emails it to parent/student.
    Registered as a Celery task — triggered after successful payment verification.
    """
    from .models import FeePayment, FeeReceipt

    try:
        payment = FeePayment.objects.select_related(
            'student__parent', 'student__parent__user',
            'student__user', 'fee_structure__fee_type', 'school'
        ).get(pk=fee_payment_id)
    except FeePayment.DoesNotExist:
        logger.error(f"FeePayment {fee_payment_id} not found.")
        return

    # Avoid duplicate receipts
    if hasattr(payment, 'receipt'):
        logger.info(f"Receipt already exists for payment {fee_payment_id}")
        return

    receipt_number = _generate_receipt_number(payment.school_id)
    receipt = FeeReceipt.objects.create(
        fee_payment=payment,
        school_id=payment.school_id,
        receipt_number=receipt_number,
    )

    pdf_buffer = _build_receipt_pdf(payment)

    # Email targets
    recipients = []
    if payment.student.user and payment.student.user.email:
        recipients.append(payment.student.user.email)
    if (hasattr(payment.student, 'parent') and payment.student.parent
            and payment.student.parent.user and payment.student.parent.user.email):
        recipients.append(payment.student.parent.user.email)

    if recipients and pdf_buffer:
        email = EmailMessage(
            subject=f"[{settings.SCHOOL_NAME}] Fee Receipt {receipt_number}",
            body=(
                f"Dear Parent/Student,\n\n"
                f"Your fee payment of ₹{payment.amount_paid} has been received.\n"
                f"Receipt No: {receipt_number}\n\n"
                f"Thank you."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        email.attach(f"{receipt_number}.pdf", pdf_buffer.read(), 'application/pdf')
        try:
            email.send()
            logger.info(f"Receipt emailed to {recipients}")
        except Exception as exc:
            logger.error(f"Email failed: {exc}")
            raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_webhook_event(self, order_id, payment_id, event_payload):
    """
    Processes a Razorpay payment.captured webhook event asynchronously.
    Ensures idempotency — checks if payment already processed.
    """
    from .models import RazorpayOrder, PaymentAuditLog, FeePayment, FeeReceipt
    from core.choices import RazorpayOrderStatus, PaymentAuditType
    import razorpay

    try:
        order = RazorpayOrder.objects.get(razorpay_order_id=order_id)
    except RazorpayOrder.DoesNotExist:
        logger.warning(f"Webhook for unknown order: {order_id}")
        return

    if order.status == RazorpayOrderStatus.PAID:
        logger.info(f"Order {order_id} already processed — skipping.")
        return

    PaymentAuditLog.objects.create(
        razorpay_order=order,
        event_type=PaymentAuditType.WEBHOOK_RECEIVED,
        razorpay_payment_id=payment_id,
        payload_json=event_payload,
    )

    # Generate receipt async
    if order.fee_payment_id:
        generate_and_send_receipt.delay(order.fee_payment_id)
