import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
try:
    django.setup()
    from django.contrib import admin
    print("Registered models:")
    for model, model_admin in admin.site._registry.items():
        print(f"- {model._meta.app_label}.{model._meta.model_name}")
except Exception as e:
    import traceback
    traceback.print_exc()
