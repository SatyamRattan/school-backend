from django.db import models
from core.models import TenantManager
from core.choices import SubscriptionPlan, SubscriptionStatus, PaymentStatus

def upload_school_logo(instance, filename):
    return f'school_logos/{instance.code}/{filename}'

class School(models.Model):
    name = models.CharField(max_length=255)
    code = models.SlugField(unique=True) # e.g., 'sunrise'
    logo = models.ImageField(upload_to=upload_school_logo, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class TenantDatabase(models.Model):
    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name='database')
    db_name = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.school.name} -> {self.db_name}"

class CustomDomain(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='domains')
    domain = models.CharField(max_length=255, unique=True) # e.g., 'sunrisepublicschool.edu.in'
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return self.domain

class Subscription(models.Model):
    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(max_length=10, choices=SubscriptionPlan.choices, default=SubscriptionPlan.MONTHLY)
    start_date = models.DateField()
    expiry_date = models.DateField()
    grace_period_end_date = models.DateField(blank=True, null=True)
    auto_renew = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.ACTIVE)

    objects = TenantManager()

    def __str__(self):
        return f"{self.school.name} - {self.plan} until {self.expiry_date}"

class PaymentTransaction(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='payments')
    order_id = models.CharField(max_length=100, unique=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = TenantManager()

    def __str__(self):
        return f"{self.order_id} - {self.status}"
