import csv
import io
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import Student, Parent
from datetime import datetime

User = get_user_model()

REQUIRED_HEADERS = [
    'first_name', 'last_name', 'email', 'date_of_birth', 
    'gender', 'admission_number', 'parent_email', 
    'parent_name', 'parent_phone'
]

def parse_csv(file):
    """
    Parses uploaded CSV file and returns list of dictionaries.
    """
    decoded_file = file.read().decode('utf-8')
    io_string = io.StringIO(decoded_file)
    reader = csv.DictReader(io_string)
    
    # Validate Headers
    headers = reader.fieldnames
    missing = [h for h in REQUIRED_HEADERS if h not in headers]
    if missing:
        raise ValueError(f"Missing headers: {', '.join(missing)}")
        
    return list(reader)

def process_bulk_import(rows, school_id):
    """
    Iterates rows and creates Student/Parent.
    Returns summary dict.
    """
    summary = {
        "total": len(rows),
        "success": 0,
        "failed": 0,
        "errors": []
    }
    
    for index, row in enumerate(rows):
        line_num = index + 2 # Header is line 1
        try:
            with transaction.atomic():
                # 1. Create/Get Parent User & Profile
                parent_email = row['parent_email']
                parent_user, created = User.objects.get_or_create(
                    username=parent_email.split('@')[0], # Simple username
                    email=parent_email,
                    defaults={
                        'first_name': row['parent_name'].split(' ')[0], 
                        'last_name': row['parent_name'].split(' ')[-1] if ' ' in row['parent_name'] else '',
                        'role': 'PARENT',
                        'school_id': school_id,
                        'phone_number': row['parent_phone']
                    }
                )
                if created:
                    parent_user.set_password("parent123") # Default password
                    parent_user.save()
                
                parent_profile, _ = Parent.objects.get_or_create(
                    user=parent_user,
                    defaults={'address': 'Address Pending'}
                )
                
                # 2. Create Student User & Profile
                student_email = row['email']
                if User.objects.filter(email=student_email).exists():
                    raise ValueError(f"Email {student_email} already exists.")
                    
                student_user = User.objects.create(
                    username=row['admission_number'], # Admission No as username
                    email=student_email,
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    role='STUDENT',
                    school_id=school_id,
                    date_joined=datetime.now()
                )
                student_user.set_password("student123")
                student_user.save()
                
                # Parse Date
                dob = datetime.strptime(row['date_of_birth'], '%Y-%m-%d').date()
                
                Student.objects.create(
                    user=student_user,
                    admission_number=row['admission_number'],
                    date_of_birth=dob,
                    gender=row['gender'][0].upper(), # M/F
                    parent=parent_profile,
                    address=parent_profile.address
                )
                
                summary['success'] += 1
                
        except Exception as e:
            summary['failed'] += 1
            summary['errors'].append({
                "line": line_num,
                "email": row.get('email', 'N/A'),
                "error": str(e)
            })
            
    return summary
