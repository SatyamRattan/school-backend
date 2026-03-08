from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from students.models import Student, StudentAttendance, Parent
from teachers.models import Teacher, TeacherAttendance
from finance.models import FeePayment, FeeType, FeeStructure
from management.models import School
from .services import get_dashboard_stats

class AnalyticsServicesTest(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Test School", code="TS01")
        self.parent = Parent.objects.create(
            first_name="Peter",
            last_name="Doe",
            email="peter@example.com",
            school_id=self.school.id
        )
        self.student = Student.objects.create(
            first_name="John", 
            last_name="Doe", 
            admission_number="ST001",
            date_of_birth="2010-01-01",
            gender="M",
            parent=self.parent,
            school_id=self.school.id
        )
        self.teacher = Teacher.objects.create(
            first_name="Jane",
            last_name="Smith",
            employee_id="T001",
            date_of_joining="2020-01-01",
            school_id=self.school.id
        )
        self.fee_type = FeeType.objects.create(name="Tuition", school_id=self.school.id)
        self.fee_structure = FeeStructure.objects.create(
            fee_type=self.fee_type,
            academic_year="2024",
            amount=Decimal("5000.00"),
            due_date="2024-12-31",
            school_id=self.school.id
        )

    def test_get_dashboard_stats_basic_counts(self):
        """Verify that basic student and teacher counts are accurate."""
        stats = get_dashboard_stats(school_id=self.school.id)
        self.assertEqual(stats['counts']['students'], Student.objects.filter(school_id=self.school.id).count())
        self.assertEqual(stats['counts']['teachers'], Teacher.objects.filter(school_id=self.school.id).count())

    def test_revenue_calculation(self):
        """Check that revenue aggregation correctly sums payments."""
        FeePayment.objects.create(
            student=self.student,
            fee_structure=self.fee_structure,
            amount_paid=Decimal("1500.00"),
            payment_date=timezone.now().date(),
            school_id=self.school.id
        )
        FeePayment.objects.create(
            student=self.student,
            fee_structure=self.fee_structure,
            amount_paid=Decimal("500.50"),
            payment_date=timezone.now().date(),
            school_id=self.school.id
        )
        
        stats = get_dashboard_stats(school_id=self.school.id)
        self.assertEqual(stats['finance']['total_revenue'], 2000.5)

    def test_attendance_trend_batching(self):
        """Verify the optimized attendance trend calculation logic."""
        today = timezone.now().date()
        # Create record for today (PRESENT)
        StudentAttendance.objects.create(
            student=self.student,
            date=today,
            status='PRESENT',
            school_id=self.school.id
        )
        # Create record for yesterday (ABSENT)
        yesterday = today - timedelta(days=1)
        StudentAttendance.objects.create(
            student=self.student,
            date=yesterday,
            status='ABSENT',
            school_id=self.school.id
        )
        
        stats = get_dashboard_stats(school_id=self.school.id)
        
        # Trend is last 7 days. Today is the last element (index 6)
        self.assertEqual(stats['charts']['attendance']['data'][6], 100.0)
        # Yesterday is index 5
        self.assertEqual(stats['charts']['attendance']['data'][5], 0.0)
        # Other days should be 0.0
        self.assertEqual(stats['charts']['attendance']['data'][4], 0.0)

    def test_empty_school_safety(self):
        """Ensure the service doesn't crash if a school has no data."""
        new_school = School.objects.create(name="Empty School", code="ES01")
        try:
            stats = get_dashboard_stats(school_id=new_school.id)
            self.assertEqual(stats['counts']['students'], 0)
            self.assertEqual(stats['finance']['total_revenue'], 0.0)
            self.assertEqual(len(stats['charts']['attendance']['data']), 7)
        except Exception as e:
            self.fail(f"get_dashboard_stats crashed for empty school: {e}")
