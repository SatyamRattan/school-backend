import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from management.models import School, TenantDatabase

print("Listing Tenant Databases:")
for school in School.objects.all():
    td = TenantDatabase.objects.filter(school=school).first()
    db_name = td.db_name if td else "None"
    print(f"School: {school.name} | Code: {school.code} | DB: {db_name}")
