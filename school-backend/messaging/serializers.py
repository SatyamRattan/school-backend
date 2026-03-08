from rest_framework import serializers
from .models import Conversation, Message
from django.contrib.auth import get_user_model

User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    sender_role = serializers.CharField(source='sender.role', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_name', 'sender_role', 'text', 'timestamp']
        read_only_fields = ['sender', 'timestamp']


class ConversationSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'created_at', 'last_message', 'other_participant']

    def get_last_message(self, obj):
        last = obj.messages.last()
        if last:
            return {'text': last.text, 'timestamp': last.timestamp}
        return None

    def get_other_participant(self, obj):
        request = self.context.get('request')
        if not request:
            return None
        other = obj.participants.exclude(id=request.user.id).first()
        if other:
            return {'id': other.id, 'name': other.get_full_name(), 'role': other.role}
        return None
