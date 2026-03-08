from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Teacher, TeacherAttendance, StaffLeave, Payroll
from .serializers import TeacherSerializer, TeacherAttendanceSerializer, StaffLeaveSerializer, PayrollSerializer
from core.permissions import IsSchoolStaff, IsSchoolAdmin


class TeacherViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolAdmin]
    filterset_fields = ['is_active', 'joining_date', 'school_id']
    search_fields = ['first_name', 'last_name', 'employee_id', 'subject_specialization']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Teacher.objects.all()
        if hasattr(user, 'school_id') and user.school_id:
            return Teacher.objects.filter(school_id=user.school_id)
        return Teacher.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'school_id') and user.school_id:
            serializer.save(school_id=user.school_id)
        else:
            serializer.save()


class TeacherAttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolStaff]
    filterset_fields = ['teacher', 'date', 'status', 'school_id']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return TeacherAttendance.objects.all()
        if hasattr(user, 'school_id') and user.school_id:
            return TeacherAttendance.objects.filter(school_id=user.school_id)
        return TeacherAttendance.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'school_id') and user.school_id:
            serializer.save(school_id=user.school_id)
        else:
            serializer.save()

class StaffLeaveViewSet(viewsets.ModelViewSet):
    serializer_class = StaffLeaveSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['teacher', 'status', 'school_id']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return StaffLeave.objects.all()
            
        base_qs = StaffLeave.objects.filter(school_id=user.school_id) if hasattr(user, 'school_id') else StaffLeave.objects.none()
        
        # Admins can see all leaves for the school
        if user.role in ['PLATFORM_ADMIN', 'SCHOOL_ADMIN', 'ACCOUNTANT']:
            return base_qs
            
        # Teachers only see their own
        if hasattr(user, 'teacher_profile'):
            return base_qs.filter(teacher=user.teacher_profile)
            
        return StaffLeave.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        kwargs = {}
        if hasattr(user, 'school_id') and user.school_id:
            kwargs['school_id'] = user.school_id
        if hasattr(user, 'teacher_profile') and user.role == 'TEACHER':
            kwargs['teacher'] = user.teacher_profile
            
        serializer.save(**kwargs)

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated, IsSchoolAdmin])
    def approve(self, request, pk=None):
        leave = self.get_object()
        action_status = request.data.get('status')
        admin_remarks = request.data.get('admin_remarks', '')

        if action_status not in ['APPROVED', 'REJECTED']:
            return Response({"error": "Status must be APPROVED or REJECTED"}, status=status.HTTP_400_BAD_REQUEST)

        leave.status = action_status
        leave.admin_remarks = admin_remarks
        
        from django.utils import timezone
        leave.reviewed_on = timezone.now()
        leave.save()

        return Response({"message": f"Leave {action_status.lower()} successfully."})

class PayrollViewSet(viewsets.ModelViewSet):
    serializer_class = PayrollSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['teacher', 'status', 'month', 'school_id']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Payroll.objects.all()
            
        base_qs = Payroll.objects.filter(school_id=user.school_id) if hasattr(user, 'school_id') else Payroll.objects.none()
        
        if user.role in ['PLATFORM_ADMIN', 'SCHOOL_ADMIN', 'ACCOUNTANT']:
            return base_qs
            
        if hasattr(user, 'teacher_profile'):
            return base_qs.filter(teacher=user.teacher_profile)
            
        return Payroll.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'school_id') and user.school_id:
            serializer.save(school_id=user.school_id)
        else:
            serializer.save()
