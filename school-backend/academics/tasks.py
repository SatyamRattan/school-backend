import pandas as pd
from celery import shared_task
from django.db import transaction
from django.core.files.storage import default_storage
from students.models import Student
from .models import Exam, Subject, ExamResult, Classroom
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_bulk_marks_upload(file_path, school_id, exam_id, subject_id, teacher_id):
    """
    Parses an Excel/CSV file and creates/updates ExamResult records.
    """
    try:
        # 1. Load data
        file_content = default_storage.open(file_path)
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_content)
        else:
            df = pd.read_excel(file_content)
            
        exam = Exam.objects.get(id=exam_id, school_id=school_id)
        subject = Subject.objects.get(id=subject_id, school_id=school_id)
        
        results_to_create = []
        errors = []
        
        # Expected columns: admission_number, marks_obtained, max_marks
        with transaction.atomic():
            for index, row in df.iterrows():
                admission_no = str(row.get('admission_number')).strip()
                marks = row.get('marks_obtained')
                max_m = row.get('max_marks', 100)
                
                try:
                    student = Student.objects.get(admission_number=admission_no, school_id=school_id)
                    
                    # Update or Create
                    ExamResult.objects.update_or_create(
                        student=student,
                        exam=exam,
                        subject=subject,
                        defaults={
                            'school_id': school_id,
                            'marks_obtained': marks,
                            'max_marks': max_m
                        }
                    )
                except Student.DoesNotExist:
                    errors.append(f"Row {index+1}: Student with admission number {admission_no} not found.")
                except Exception as e:
                    errors.append(f"Row {index+1}: Error processing - {str(e)}")
                    
        # 2. Cleanup file
        default_storage.delete(file_path)
        
        return {
            "status": "completed",
            "processed_count": len(df) - len(errors),
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Bulk marks upload failed: {str(e)}")
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
        return {"status": "failed", "error": str(e)}
