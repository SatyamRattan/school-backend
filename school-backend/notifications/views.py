from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer
from .services import send_notification
from core.permissions import IsSchoolStaff
from users.models import User
from management.models import School
from core.choices import UserRole
from students.models import Student


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Scoped strictly to the authenticated user's notifications
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=['patch'])
    def read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})

    @action(detail=False, methods=['patch'])
    def read_all(self, request):
        self.get_queryset().update(is_read=True)
        return Response({'status': 'all marked as read'})

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsSchoolStaff])
    def bulk_send(self, request):
        """
        Send a notification to a group of users.
        Payload:
        {
            "title": "Welcome Back",
            "message": "School reopens tomorrow.",
            "target_role": "STUDENT", # Optional (ALL, TEACHER, STUDENT, PARENT)
            "target_classroom": 1,    # Optional (Classroom ID)
            "channels": ["in_app", "email"]
        }
        """
        title = request.data.get('title')
        message = request.data.get('message')
        target_role = request.data.get('target_role')
        target_classroom = request.data.get('target_classroom')
        channels = request.data.get('channels', ['in_app'])

        if not title or not message:
            return Response({"error": "Title and message are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Base user queryset scoped to the current active school
        users = User.objects.all()
        school_id = getattr(request.user, 'school_id', None)
        if school_id:
            users = users.filter(school_id=school_id)

        # Filter by Role
        if target_role and target_role != "ALL":
            if target_role == "TEACHER":
                # When targeting 'Teachers', we usually mean 'Faculty & Staff'
                users = users.filter(role__in=[UserRole.TEACHER, UserRole.ACCOUNTANT, UserRole.SCHOOL_ADMIN])
            else:
                users = users.filter(role=target_role)

        # Filter by Classroom (Applies mainly to STUDENTS and their PARENTS)
        if target_classroom:
            student_user_ids = Student.objects.filter(classroom_id=target_classroom, user__isnull=False).values_list('user_id', flat=True)
            parent_user_ids = Student.objects.filter(classroom_id=target_classroom, parent__isnull=False, parent__user__isnull=False).values_list('parent__user_id', flat=True)
            
            combined_ids = list(student_user_ids) + list(parent_user_ids)
            users = users.filter(id__in=combined_ids)

        from .tasks import bulk_send_notifications_task
        
        user_ids = list(users.values_list('id', flat=True))
        bulk_send_notifications_task.delay(
            user_ids=user_ids,
            title=title,
            message=message,
            notification_type='GENERAL',
            channels=channels
        )

        return Response({
            "message": "Notifications enqueued for delivery.",
            "enqueued_count": len(user_ids)
        })
