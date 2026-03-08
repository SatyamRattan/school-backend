from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from students.models import Student, StudentAttendance
from teachers.models import Teacher, TeacherAttendance
from finance.models import FeePayment


def _to_float(value):
    """Safely convert Decimal or None to a float."""
    if value is None:
        return 0.0
    return float(value)


def get_dashboard_stats(school_id=None):
    """
    Returns dashboard statistics scoped to school_id (or global if None).
    All values are JSON-serialisable primitives.
    """
    today = timezone.now().date()
    start_of_month = today.replace(day=1)

    # ── Base querysets ─────────────────────────────────────────────────────────
    if school_id:
        students_qs     = Student.objects.filter(school_id=school_id)
        teachers_qs     = Teacher.objects.filter(school_id=school_id)
        payments_qs     = FeePayment.objects.filter(school_id=school_id)
        student_att_qs  = StudentAttendance.objects.filter(school_id=school_id)
        teacher_att_qs  = TeacherAttendance.objects.filter(school_id=school_id)
    else:
        students_qs     = Student.objects.all()
        teachers_qs     = Teacher.objects.all()
        payments_qs     = FeePayment.objects.all()
        student_att_qs  = StudentAttendance.objects.all()
        teacher_att_qs  = TeacherAttendance.objects.all()

    # ── Counts ─────────────────────────────────────────────────────────────────
    total_students = students_qs.count()
    total_teachers = teachers_qs.count()

    # ── Finance ────────────────────────────────────────────────────────────────
    total_revenue = _to_float(
        payments_qs.aggregate(total=Sum('amount_paid'))['total']
    )
    monthly_revenue = _to_float(
        payments_qs.filter(payment_date__gte=start_of_month)
                   .aggregate(total=Sum('amount_paid'))['total']
    )

    # ── Recent payments (last 5) ───────────────────────────────────────────────
    recent_qs = (
        payments_qs
        .select_related('student', 'fee_structure__fee_type')
        .order_by('-payment_date')[:5]
    )

    recent_payments_data = []
    for p in recent_qs:
        try:
            student_name = f"{p.student.first_name} {p.student.last_name}"
        except Exception:
            student_name = "Unknown Student"

        try:
            fee_type_name = p.fee_structure.fee_type.name
        except Exception:
            fee_type_name = "Fee Payment"

        recent_payments_data.append({
            'student': student_name,
            'amount': str(p.amount_paid),          # Decimal → str (safe for JSON)
            'date': p.payment_date.isoformat(),    # date → ISO string
            'type': fee_type_name,
        })

    # ── Attendance trend (last 7 days) ─────────────────────────────────────────
    attendance_labels = []
    attendance_data   = []

    # Calculate date range
    days_to_fetch = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    start_date = days_to_fetch[0]

    # Batch fetch attendance counts grouped by date and status
    from django.db.models import Count
    
    def get_attendance_counts(queryset, start):
        return (
            queryset.filter(date__gte=start)
            .values('date', 'status')
            .annotate(count=Count('id'))
        )

    s_counts = get_attendance_counts(student_att_qs, start_date)
    t_counts = get_attendance_counts(teacher_att_qs, start_date)

    # Map to structured dict: { date: { 'TOTAL': X, 'PRESENT': Y } }
    stats_map = {}
    for entry in list(s_counts) + list(t_counts):
        d = entry['date']
        if d not in stats_map: stats_map[d] = {'TOTAL': 0, 'PRESENT': 0}
        stats_map[d]['TOTAL'] += entry['count']
        if entry['status'] == 'PRESENT':
            stats_map[d]['PRESENT'] += entry['count']

    for day in days_to_fetch:
        attendance_labels.append(day.strftime('%d %b'))
        day_stats = stats_map.get(day, {'TOTAL': 0, 'PRESENT': 0})
        
        total = day_stats['TOTAL']
        present = day_stats['PRESENT']
        pct = round(present / total * 100, 1) if total > 0 else 0.0
        attendance_data.append(pct)

    return {
        'counts': {
            'students': total_students,
            'teachers': total_teachers,
        },
        'finance': {
            'total_revenue':   total_revenue,
            'monthly_revenue': monthly_revenue,
        },
        'activity': {
            'recent_payments': recent_payments_data,
        },
        'charts': {
            'attendance': {
                'labels': attendance_labels,
                'data':   attendance_data,
            }
        },
    }
