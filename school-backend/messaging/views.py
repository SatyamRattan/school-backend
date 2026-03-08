from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.contrib.auth import get_user_model

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from students.models import Student
from academics.models import TeacherAssignment

User = get_user_model()


class IsParentRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'PARENT'


class IsParticipant(permissions.BasePermission):
    """Ensures users can only access conversations they are part of."""
    def has_object_permission(self, request, view, obj):
        return request.user in obj.participants.all()


class ConversationViewSet(viewsets.ModelViewSet):
    """
    A viewset for parent-teacher conversations.
    Parents can only start conversations with teachers of their children.
    """
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related('participants', 'messages').order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """
        Create or retrieve a conversation with a specific teacher.
        Validates that the parent can only message their child's teacher.
        """
        teacher_id = request.data.get('teacher_id')
        if not teacher_id:
            return Response({'error': 'teacher_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.role == 'PARENT':
            # Security: ensure the teacher is assigned to one of the parent's children
            children = Student.objects.filter(parent__user=request.user)
            is_assigned = TeacherAssignment.objects.filter(
                teacher_id=teacher_id,
                classroom__in=[s.classroom for s in children if s.classroom]
            ).exists()
            if not is_assigned:
                return Response(
                    {'error': 'You can only message teachers assigned to your child.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        teacher = User.objects.get(pk=teacher_id)

        # Find existing conversation between these two users
        existing = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=teacher
        ).filter(
            participants__count=2
        ).first()

        if not existing:
            conversation = Conversation.objects.create()
            conversation.participants.add(request.user, teacher)
            serializer = self.get_serializer(conversation, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        serializer = self.get_serializer(existing, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get', 'post'], url_path='messages')
    def messages(self, request, pk=None):
        conversation = self.get_object()

        if not request.user in conversation.participants.all():
            return Response({'error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'GET':
            msgs = conversation.messages.order_by('timestamp')
            serializer = MessageSerializer(msgs, many=True)
            return Response(serializer.data)

        if request.method == 'POST':
            serializer = MessageSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(sender=request.user, conversation=conversation)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
