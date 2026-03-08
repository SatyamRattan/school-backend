import os
import django
from django.utils import timezone
from datetime import timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import User
from management.models import School, Subscription, TenantDatabase
from core.choices import UserRole

def create_test_users():
    # 1. Ensure a school exists
    school, created = School.objects.get_or_create(
        code='sunrise',
        defaults={'name': 'Sunrise Public School'}
    )
    if created:
        print(f"Created school: {school.name}")
        # Add a placeholder subscription
        Subscription.objects.create(
            school=school,
            start_date=timezone.now().date(),
            expiry_date=(timezone.now() + timedelta(days=365)).date()
        )
        # Placeholder Tenant Database
        TenantDatabase.objects.get_or_create(
            school=school,
            defaults={'db_name': 'sunrise_db'}
        )
    else:
        print(f"Using existing school: {school.name}")

    roles = [
        ('platform_admin', UserRole.PLATFORM_ADMIN, None),
        ('school_admin', UserRole.SCHOOL_ADMIN, school.id),
        ('accountant', UserRole.ACCOUNTANT, school.id),
        ('teacher_user', UserRole.TEACHER, school.id),
        ('student_user', UserRole.STUDENT, school.id),
        ('parent_user', UserRole.PARENT, school.id),
    ]

    password = 'Password123!'

    for username, role, s_id in roles:
        user, u_created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f"{username}@example.com",
                'role': role,
                'school_id': s_id,
                'is_staff': role in [UserRole.PLATFORM_ADMIN, UserRole.SCHOOL_ADMIN, UserRole.TEACHER, UserRole.ACCOUNTANT],
                'is_superuser': role == UserRole.PLATFORM_ADMIN
            }
        )
        if u_created:
            user.set_password(password)
            user.save()
            print(f"Created user: {username} with role {role}")
        else:
            print(f"User {username} already exists")

if __name__ == '__main__':
    create_test_users()
