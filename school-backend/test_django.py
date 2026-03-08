import os
import django
import sys

try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()
    print("Django setup successful")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
