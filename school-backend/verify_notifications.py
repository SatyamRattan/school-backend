import os
import django
import sys

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from notifications.services import send_notification
from notifications.models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

def verify_notifications():
    print("🔔 Verifying Notification System...")

    # 1. Test Service Layer
    # We use first user found to test
    user = User.objects.filter(is_active=True).first()
    if not user:
        print("❌ No active user found. Skipping service test.")
        return

    print(f"👤 Sending notification to {user.username}...")
    try:
        send_notification(
            user=user,
            title="Test Notification",
            message="This is a verification message from Antigravity.",
            notification_type="GENERAL",
            channels=['in_app', 'sms', 'email'] # Test all channels (email/sms will print to console)
        )
        print("✅ Service call successful.")
    except Exception as e:
        print(f"❌ Service call failed: {e}")
        return

    # 2. Verify DB Record
    try:
        notif = Notification.objects.filter(recipient=user, title="Test Notification").order_by('-created_at').first()
        if notif:
            print(f"✅ Notification found in DB: ID {notif.id}")
        else:
            print("❌ Notification NOT found in DB.")
    except Exception as e:
        print(f"❌ DB Check failed (Likely due to missing migrations): {e}")

if __name__ == "__main__":
    verify_notifications()
