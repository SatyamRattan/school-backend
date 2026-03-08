from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from .models import Subscription, School

@shared_task
def check_subscription_expiry():
    today = timezone.now().date()
    
    # 1. Send Renewal Reminders (30 days before expiry)
    expiring_soon = Subscription.objects.filter(expiry_date=today + timedelta(days=30), status='ACTIVE')
    for sub in expiring_soon:
        # Placeholder for email logic
        print(f"Sending renewal reminder to {sub.school.name}")
        # send_mail(...)

    # 2. Check for Expiry (Enter Grace Period)
    expired_today = Subscription.objects.filter(expiry_date=today, status='ACTIVE')
    for sub in expired_today:
        print(f"{sub.school.name} subscription expired. Entering grace period.")
        # Notify admin

    # 3. Suspend Schools (Grace Period Over)
    # Assuming 7 days grace period
    grace_period_over = Subscription.objects.filter(expiry_date=today - timedelta(days=7), status='ACTIVE')
    for sub in grace_period_over:
        print(f"Suspending {sub.school.name} due to non-payment.")
        sub.status = 'SUSPENDED'
        sub.school.is_active = False # Main switch
        sub.school.save()
        sub.save()
