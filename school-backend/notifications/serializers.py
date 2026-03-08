from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Safe outward-facing serializer — does NOT expose recipient FK or school FK
    so users only see their own notification content.
    """
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'notification_type', 'is_read', 'created_at']
        read_only_fields = ['id', 'title', 'message', 'notification_type', 'created_at']