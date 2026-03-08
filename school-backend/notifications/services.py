from django.core.mail import send_mail
from django.conf import settings
from .models import Notification

def send_notification(user, title, message, notification_type='GENERAL', channels=None):
    """
    Sends notification via specified channels (in_app, email, sms).
    Default channels: ['in_app']
    """
    if channels is None:
        channels = ['in_app']

    # 1. In-App Notification (Always created if requested)
    if 'in_app' in channels:
        Notification.objects.create(
            recipient=user,
            title=title,
            message=message,
            notification_type=notification_type
        )

    # 2. Email Notification
    if 'email' in channels and user.email:
        print(f"DEBUG: Attempting email to {user.email}")
        try:
            send_mail(
                subject=f"[{settings.SCHOOL_NAME}] {title}", # Assuming SCHOOL_NAME setting exists or we hardcode
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False # Change to False for debugging
            )
            print(f"📧 Email sent to {user.email}")
        except Exception as e:
            print(f"❌ Email failed to {user.email}: {type(e).__name__}: {str(e)}")

    # 3. SMS Notification (Stub)
    if 'sms' in channels and hasattr(user, 'phone_number') and user.phone_number:
        # Integration with Twilio/Provider would go here
        print(f"📱 [SMS STUB] To {user.phone_number}: {message}")
