import os
import django
from django.conf import settings
from django.db import connections

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Manually add sunrise_db if not present
if 'sunrise_db' not in settings.DATABASES:
    settings.DATABASES['sunrise_db'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sunrise_db',
        'USER': settings.TENANT_DB_USER,
        'PASSWORD': settings.TENANT_DB_PASSWORD,
        'HOST': settings.TENANT_DB_HOST or '127.0.0.1',
        'PORT': settings.TENANT_DB_PORT or '5432',
    }

def check_tables(db_alias):
    conn = connections[db_alias]
    print(f"Checking tables in {db_alias}...")
    
    tenant_apps = ['academics', 'students', 'teachers', 'finance']
    missing_tables = []
    
    with conn.cursor() as cursor:
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        existing_tables = [t[0] for t in cursor.fetchall()]
        
        from django.apps import apps
        for app_label in tenant_apps:
            app_config = apps.get_app_config(app_label)
            for model_name, model in app_config.models.items():
                table_name = model._meta.db_table
                if table_name not in existing_tables:
                    missing_tables.append((app_label, model_name, table_name))
    
    return missing_tables

if __name__ == '__main__':
    missing = check_tables('sunrise_db')
    print("\nMissing tables in sunrise_db:")
    for app, model, table in missing:
        print(f"- {app}.{model} (table: {table})")
