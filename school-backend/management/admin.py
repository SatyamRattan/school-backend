from django.contrib import admin
from .models import School, CustomDomain, Subscription, TenantDatabase, PaymentTransaction

admin.site.register(School)
admin.site.register(CustomDomain)
admin.site.register(Subscription)
admin.site.register(TenantDatabase)
admin.site.register(PaymentTransaction)
