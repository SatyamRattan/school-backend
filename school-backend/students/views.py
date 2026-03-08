from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.db import transaction
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

from .models import Student, Parent, StudentDocument, StudentAttendance
from .serializers import (
    StudentSerializer, ParentSerializer,
    StudentDocumentSerializer, StudentAttendanceSerializer
)
from core.permissions import IsSchoolStaff, IsSchoolAdmin, IsStudentOrParent
from .utils import parse_csv, process_bulk_import


class BulkStudentImportView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSchoolAdmin]
    parser_classes = [MultiPartParser]

    def post(self, request):
        if 'file' not in request.FILES:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['file']
        if not file.name.endswith('.csv'):
            return Response({"error": "File is not CSV type"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = parse_csv(file)
            school_id = request.user.school_id
            if not school_id:
                return Response({"error": "User does not belong to a school"}, status=status.HTTP_400_BAD_REQUEST)
            
            from .tasks import process_bulk_import_task
            process_bulk_import_task.delay(data, school_id)
            
            return Response({
                "message": "Bulk import process started in the background.",
                "total_rows": len(data)
            }, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolStaff | IsStudentOrParent]
    filterset_fields = ['classroom', 'is_active', 'gender', 'school_id']
    search_fields = ['first_name', 'last_name', 'admission_number']

    def get_queryset(self):
        user = self.request.user
        base_qs = Student.objects.select_related('parent', 'classroom').prefetch_related('documents')

        if user.is_superuser:
            return base_qs.all()
        
        school_id = getattr(user, 'school_id', None)
        if not school_id:
            return Student.objects.none()

        qs = base_qs.filter(school_id=school_id)

        if user.role == 'STUDENT':
            return qs.filter(user=user)
        if user.role == 'PARENT':
            return qs.filter(parent__user=user)
            
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'school_id') and user.school_id:
            serializer.save(school_id=user.school_id)
        else:
            serializer.save()


class ParentViewSet(viewsets.ModelViewSet):
    serializer_class = ParentSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolStaff]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Parent.objects.all()
        if hasattr(user, 'school_id') and user.school_id:
            return Parent.objects.filter(school_id=user.school_id)
        return Parent.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'school_id') and user.school_id:
            serializer.save(school_id=user.school_id)
        else:
            serializer.save()


class StudentDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentDocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolStaff]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return StudentDocument.objects.all()
        if hasattr(user, 'school_id') and user.school_id:
            return StudentDocument.objects.select_related('student').filter(student__school_id=user.school_id)
        return StudentDocument.objects.none()

    def perform_create(self, serializer):
        # FIX: was missing school_id assignment — documents were saved without tenant scope
        user = self.request.user
        if hasattr(user, 'school_id') and user.school_id:
            serializer.save(school_id=user.school_id)
        else:
            serializer.save()


class StudentAttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = StudentAttendanceSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolStaff | IsStudentOrParent]
    filterset_fields = ['student', 'date', 'status', 'school_id']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return StudentAttendance.objects.all()
        
        school_id = getattr(user, 'school_id', None)
        if not school_id:
            return StudentAttendance.objects.none()

        qs = StudentAttendance.objects.select_related('student').filter(school_id=school_id)

        if user.role == 'STUDENT':
            return qs.filter(student__user=user)
        if user.role == 'PARENT':
            return qs.filter(student__parent__user=user)

        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'school_id') and user.school_id:
            serializer.save(school_id=user.school_id)
        else:
            serializer.save()

    @action(detail=False, methods=['post'])
    def bulk_mark(self, request):
        """
        Expects a list of records: [{"student": id, "date": "...", "status": "..."}]
        """
        data = request.data
        if not isinstance(data, list):
            return Response({"error": "Expected a list of attendance records"}, status=status.HTTP_400_BAD_REQUEST)

        school_id = request.user.school_id
        if not school_id:
            return Response({"error": "User does not belong to a school"}, status=status.HTTP_400_BAD_REQUEST)

        created_count = 0
        updated_count = 0
        
        try:
            from .tasks import bulk_mark_attendance_task
            bulk_mark_attendance_task.delay(data, school_id)

            return Response({
                "message": "Bulk attendance marking process started in the background.",
                "total_records": len(data)
            }, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
