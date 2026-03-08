from celery import shared_task
from django.db import transaction
from students.models import Student
from .models import StudentRiskRecord
from .services import aggregate_student_risk_data
from .ai_engine import StudentRiskAIEngine
import logging

logger = logging.getLogger(__name__)

@shared_task
def run_student_risk_analysis(student_id):
    """
    Task to analyze risk for a specific student.
    """
    try:
        student = Student.objects.get(id=student_id)
        
        # 1. Aggregate metrics
        data = aggregate_student_risk_data(student)
        
        # 2. Get AI prediction
        engine = StudentRiskAIEngine()
        prediction = engine.get_prediction(data)
        
        # 3. Update or Create Risk Record
        with transaction.atomic():
            risk_record, created = StudentRiskRecord.objects.update_or_create(
                student=student,
                defaults={
                    'school': student.school,
                    'score': prediction.get('risk_score', 0),
                    'level': prediction.get('risk_level', 'LOW'),
                    'risk_factors': prediction.get('primary_factors', []),
                    'ai_recommendations': prediction.get('recommendations', '')
                }
            )
            
        return f"Successfully processed student {student_id}"
        
    except Exception as e:
        logger.error(f"Task failed for student {student_id}: {str(e)}")
        return str(e)

@shared_task
def run_weekly_school_risk_audit(school_id):
    """
    Coordinator task to trigger audits for all active students in a school.
    """
    active_students = Student.objects.filter(school_id=school_id, is_active=True)
    for student in active_students:
        run_student_risk_analysis.delay(student.id)
        
    return f"Triggered audit for {active_students.count()} students in school {school_id}"
