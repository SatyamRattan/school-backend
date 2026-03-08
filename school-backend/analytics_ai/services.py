from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Sum
from students.models import Student, StudentAttendance
from academics.models import ExamResult
from finance.models import FeePayment, FeeStructure

def aggregate_student_risk_data(student):
    """
    Aggregates data points for a single student to be used by the AI engine.
    """
    school = student.school
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    # 1. Attendance Trend (Last 30 days)
    attendance_records = StudentAttendance.objects.filter(
        student=student,
        date__gte=thirty_days_ago
    )
    total_days = attendance_records.count()
    present_days = attendance_records.filter(status='PRESENT').count()
    attendance_rate = (present_days / total_days * 100) if total_days > 0 else 100.0
    
    # 2. Performance Trend (Last 2 Exams)
    results = ExamResult.objects.filter(student=student).order_by('-exam__start_date')
    
    # Get subjects and calculate average marks for latest and previous exams
    exam_groups = {}
    for res in results:
        exam_id = res.exam_id
        if exam_id not in exam_groups:
            exam_groups[exam_id] = []
        exam_groups[exam_id].append(float(res.marks_obtained / res.max_marks * 100))
        
    exam_averages = [sum(marks)/len(marks) for marks in exam_groups.values()]
    latest_avg = exam_averages[0] if len(exam_averages) > 0 else None
    previous_avg = exam_averages[1] if len(exam_averages) > 1 else None
    
    performance_change = 0
    if latest_avg and previous_avg:
        performance_change = latest_avg - previous_avg
        
    # 3. Financial Risk (Fee Compliance)
    total_due = FeeStructure.objects.filter(
        school=school,
        classroom=student.classroom
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_paid = FeePayment.objects.filter(student=student).aggregate(total=Sum('amount_paid'))['total'] or 0
    fee_balance = float(total_due) - float(total_paid)
    
    return {
        "student_id": student.id,
        "metrics": {
            "attendance_rate_30d": round(attendance_rate, 2),
            "performance": {
                "latest_avg": round(latest_avg, 2) if latest_avg is not None else None,
                "change": round(performance_change, 2)
            },
            "finance": {
                "balance": round(fee_balance, 2),
                "is_delinquent": fee_balance > 0
            }
        },
        "metadata": {
            "admission_no": student.admission_number,
            "classroom": str(student.classroom)
        }
    }
