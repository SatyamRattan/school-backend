import logging
from celery import shared_task
from .utils import process_bulk_import

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    max_retries=1,
    time_limit=3600 # 1 hour for major imports
)
def process_bulk_import_task(self, data, school_id):
    """
    Asynchronous task for processing bulk student imports.
    """
    try:
        summary = process_bulk_import(data, school_id)
        logger.info(f"Bulk import completed for school {school_id}. Summary: {summary}")
        return summary
    except Exception as e:
        logger.error(f"Bulk import failed for school {school_id}: {str(e)}")
        raise e

@shared_task(
    bind=True,
    max_retries=1,
    time_limit=600 # 10 mins
)
def bulk_mark_attendance_task(self, data, school_id):
    """
    Asynchronous task for marking bulk attendance.
    """
    from django.db import transaction
    from .models import StudentAttendance
    
    created_count = 0
    updated_count = 0
    
    try:
        with transaction.atomic():
            for item in data:
                student_id = item.get('student')
                date = item.get('date')
                status_val = item.get('status')
                remarks = item.get('remarks', "")

                attendance, created = StudentAttendance.objects.update_or_create(
                    student_id=student_id,
                    date=date,
                    defaults={
                        'status': status_val,
                        'remarks': remarks,
                        'school_id': school_id
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
        return {"created": created_count, "updated": updated_count}
    except Exception as e:
        logger.error(f"Bulk attendance failed for school {school_id}: {str(e)}")
        raise e
