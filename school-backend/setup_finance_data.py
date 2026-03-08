import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_management.settings')
django.setup()

from management.models import School
from academics.models import Classroom
from students.models import Student
from finance.models import FeeType, FeeStructure
from datetime import date, timedelta

def setup_data():
    school = School.objects.filter(name='Sunrise Public School').first()
    if not school:
        school = School.objects.first()
    
    if not school:
        print("No school found.")
        return

    # 1. Create Classroom
    classroom, _ = Classroom.objects.get_or_create(
        school=school,
        name='Grade 10',
        section='A'
    )
    print(f"Classroom created: {classroom}")

    # 2. Assign Student to Classroom
    student = Student.objects.filter(admission_number='2024001').first()
    if student:
        student.classroom = classroom
        student.save()
        print(f"Student {student.first_name} assigned to {classroom}")
    else:
        print("Student not found.")

    # 3. Create Fee Type
    tuition_fee, _ = FeeType.objects.get_or_create(
        school=school,
        name='Tuition Fee',
        defaults={'description': 'Main academic tuition fee'}
    )
    
    transport_fee, _ = FeeType.objects.get_or_create(
        school=school,
        name='Transport Fee',
        defaults={'description': 'School bus service fee'}
    )
    print("Fee types created/found.")

    # 4. Create Fee Structures
    FeeStructure.objects.get_or_create(
        school=school,
        fee_type=tuition_fee,
        classroom=classroom,
        academic_year='2025-26',
        defaults={
            'amount': 5000.00,
            'due_date': date.today() + timedelta(days=30)
        }
    )
    
    FeeStructure.objects.get_or_create(
        school=school,
        fee_type=transport_fee,
        classroom=classroom,
        academic_year='2025-26',
        defaults={
            'amount': 1200.00,
            'due_date': date.today() + timedelta(days=15)
        }
    )
    print("Fee structures created.")

if __name__ == "__main__":
    setup_data()
