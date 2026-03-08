from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Q

from .models import Student, StudentAttendance, BehaviorReport
from .serializers import StudentSerializer, StudentAttendanceSerializer, BehaviorReportSerializer


class IsParent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'PARENT'


class ParentScopeMixin:
    """
    A mixin that restricts all querysets to only data belonging
    to the authenticated parent's children. Zero cross-parent data leakage.
    """
    def get_children(self):
        return Student.objects.filter(parent__user=self.request.user)


class ParentOverviewView(ParentScopeMixin, APIView):
    """
    Aggregated overview: all children with summary stats.
    GET /api/parent/overview/
    """
    permission_classes = [IsParent]

    def get(self, request):
        children = self.get_children().select_related('classroom')
        data = []
        for student in children:
            attendance = StudentAttendance.objects.filter(student=student)
            total = attendance.count()
            present = attendance.filter(status='PRESENT').count()
            attendance_pct = round((present / total) * 100, 1) if total > 0 else 0

            recent_behavior = BehaviorReport.objects.filter(student=student).order_by('-date').first()

            data.append({
                'id': student.id,
                'name': str(student),
                'admission_number': student.admission_number,
                'classroom': str(student.classroom) if student.classroom else None,
                'attendance_percentage': attendance_pct,
                'attendance_total': total,
                'attendance_present': present,
                'latest_behavior': {
                    'type': recent_behavior.incident_type,
                    'comment': recent_behavior.comment,
                    'date': recent_behavior.date,
                } if recent_behavior else None,
            })
        return Response({'children': data})


class ParentAttendanceView(ParentScopeMixin, generics.ListAPIView):
    """
    List attendance for a specific child.
    GET /api/parent/attendance/?student_id=<id>
    """
    permission_classes = [IsParent]
    serializer_class = StudentAttendanceSerializer

    def get_queryset(self):
        children = self.get_children()
        student_id = self.request.query_params.get('student_id')
        qs = StudentAttendance.objects.filter(student__in=children)
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs.select_related('student').order_by('-date')


class ParentBehaviorView(ParentScopeMixin, generics.ListAPIView):
    """
    List behavior reports for a specific child.
    GET /api/parent/behavior/?student_id=<id>
    """
    permission_classes = [IsParent]
    serializer_class = BehaviorReportSerializer

    def get_queryset(self):
        children = self.get_children()
        student_id = self.request.query_params.get('student_id')
        qs = BehaviorReport.objects.filter(student__in=children)
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs.select_related('student', 'teacher')


class BehaviorReportViewSet(viewsets.ModelViewSet):
    """
    Teachers can create/read behavior reports for their school students.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BehaviorReportSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'TEACHER':
            return BehaviorReport.objects.filter(
                school_id=user.school_id
            ).select_related('student', 'teacher')
        if user.role in ['SCHOOL_ADMIN', 'PLATFORM_ADMIN'] or user.is_superuser:
            return BehaviorReport.objects.filter(
                school_id=user.school_id
            ).select_related('student', 'teacher')
        return BehaviorReport.objects.none()

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user, school_id=self.request.user.school_id)
