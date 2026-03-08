import os
import django
import psycopg2
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.apps import apps

def sync_db(db_name):
    print(f"Syncing {db_name} via psycopg2...")
    
    # Get connection params from settings
    # Since we set these in .env and settings.py reads them:
    user = settings.TENANT_DB_USER
    password = settings.TENANT_DB_PASSWORD
    host = settings.TENANT_DB_HOST or '127.0.0.1'
    port = settings.TENANT_DB_PORT or '5432'
    
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port,
            connect_timeout=5
        )
        conn.autocommit = True
    except Exception as e:
        print(f"Failed to connect to {db_name}: {e}")
        return

    tenant_apps = ['academics', 'students', 'teachers', 'finance']
    
    with conn.cursor() as cursor:
        for app_label in tenant_apps:
            try:
                app_config = apps.get_app_config(app_label)
            except LookupError:
                print(f"App {app_label} not found. Skipping.")
                continue
                
            for model_name, model in app_config.models.items():
                table_name = model._meta.db_table
                
                # Check if table exists
                cursor.execute(f"SELECT to_regclass('public.{table_name}');")
                if cursor.fetchone()[0] is None:
                    print(f"Table {table_name} missing entirely. Skipping.")
                    continue
                
                # Get all fields in the model
                for field in model._meta.fields:
                    if not hasattr(field, 'column'):
                        continue
                    
                    column_name = field.column
                    
                    # Check if column exists
                    cursor.execute(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = '{table_name}' AND column_name = '{column_name}';
                    """)
                    
                    if cursor.fetchone() is None:
                        print(f"Adding column {column_name} to {table_name}...")
                        
                        # Determine type
                        col_type = "varchar(255)" # default
                        internal_type = field.get_internal_type()
                        
                        if internal_type in ['BigAutoField', 'ForeignKey', 'OneToOneField', 'BigIntegerField', 'PositiveBigIntegerField']:
                            col_type = "bigint"
                        elif internal_type in ['IntegerField', 'PositiveIntegerField']:
                            col_type = "integer"
                        elif internal_type == 'BooleanField':
                            col_type = "boolean"
                        elif internal_type == 'DateField':
                            col_type = "date"
                        elif internal_type == 'DateTimeField':
                            col_type = "timestamp with time zone"
                        elif internal_type == 'TextField':
                            col_type = "text"
                        elif internal_type == 'DecimalField':
                            col_type = f"numeric({field.max_digits}, {field.decimal_places})"
                        
                        try:
                            # We don't add NOT NULL or FOREIGN KEY constraints to minimize issues
                            # especially cross-DB constraints which are impossible.
                            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {col_type} NULL;")
                            print(f"Successfully added {column_name} to {table_name}.")
                        except Exception as e:
                            print(f"Error adding {column_name} to {table_name}: {e}")

    conn.close()
    print(f"Finished syncing {db_name}")

if __name__ == '__main__':
    # Sync both just in case
    sync_db('sms_central_db')
    sync_db('sunrise_db')
