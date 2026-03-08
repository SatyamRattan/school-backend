from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import FileResponse

from .models import (
    Classroom, Subject, Timetable, Exam,
    ExamResult, LibraryBook, TransportRoute, TeacherAssignment,
    SchoolEvent, GradebookEntry
)
from .serializers import (
    ClassroomSerializer, SubjectSerializer, TimetableSerializer,
    ExamSerializer, ExamResultSerializer,
    LibraryBookSerializer, TransportRouteSerializer, TeacherAssignmentSerializer,
    SchoolEventSerializer, GradebookEntrySerializer
)
from core.permissions import IsSchoolStaff, IsStudentOrParent
from students.models import Student
from .utils import generate_report_card_pdf


class ClassroomViewSet(viewsets.ModelViewSet):
    serializer_class = ClassroomSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolStaff]
    search_fields = ['name', 'grade', 'section']
    filterset_fields = ['school_id']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Classroom.objects.all()
        if hasattr(user, 'school_id') and user.school_id:
            return Classroom.objects.filter(school_id=user.school_id)
        return Classroom.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'school_id') and user.school_id:
            serializer.save(school_id=user.school_id)
        else:
            serializer.save()


class SubjectViewSet(viewsets.ModelViewSet):
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolStaff]
    search_fields = ['name', 'code']
    filterset_fields = ['school_id']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Subject.objects.all()
        if hasattr(user, 'school_id') and user.school_id:
            return Subject.objects.filter(school_id=user.school_id)
        return Subject.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'school_id') and user.school_id:
            serializer.save(school_id=user.school_id)
        else:
            serializer.save()


class TimetableViewSet(viewsets.ModelViewSet):
    serializer_class = TimetableSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolStaff]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Timetable.objects.all()
        if hasattr(user, 'school_id') and user.school_id:
            return Timetable.objects.filter(school_id=user.school_id)
        return Timetable.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'school_id') and user.school_id:
            serializer.save(school_id=user.school_id)
        else:
            serializer.save()


class ExamViewSet(viewsets.ModelViewSet):
    serializer_class = ExamSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolStaff]
    search_fields = ['name']
    filterset_fields = ['school_id']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Exam.objects.all()
        if hasattr(user, 'school_id') and user.school_id:
            return Exam.objects.filter(school_id=user.school_id)
        return Exam.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'school_id') and user.school_id:
            serializer.save(school_id=user.school_id)
        else:
            serializer.save()


class ExamResultViewSet(viewsets.ModelViewSet):
    serializer_class = ExamResultSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolStaff | IsStudentOrParent]
    filterset_fields = ['exam', 'subject', 'student', 'school_id']
    search_fields = ['student__first_name', 'student__last_name']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return ExamResult.objects.select_related('student', 'exam', 'subject').all()
        
        school_id = getattr(user, 'school_id', None)
        if not school_id:
            return ExamResult.objects.none()

        qs = ExamResult.objects.select_related('student', 'exam', 'subject').filter(school_id=school_id)

        if user.role == 'STUDENT':
            return qs.filter(student__user=user)
        if user.role == 'PARENT':
            return qs.filter(student__parent__user=user)

        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'school_id') and user.school_id:
            result = serializer.save(school_id=user.school_id)
        else:
            result = serializer.save()

        from notifications.services import send_notification

        if hasattr(result.student, 'user') and result.student.user:
            send_notification(
                result.student.user,
                "Exam Result Published",
                f"Your result for {result.subject.name} in {result.exam.name} has been published. "
                f"You scored {result.marks_obtained}/{result.max_marks}.",
                notification_type='EXAM_RESULT',
                channels=['in_app']
            )

        if (hasattr(result.student, 'parent') and result.student.parent
                and hasattr(result.student.parent, 'user') and result.student.parent.user):
            send_notification(
                result.student.parent.user,
                "Exam Result Published",
                f"Result for {result.student.first_name} in {result.subject.name} "
                f"({result.exam.name}) has been published.",
                notification_type='EXAM_RESULT',
                channels=['in_app', 'email']
            )

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """
        Expects a list of results:
        [
            {"student": 1, "exam": 1, "subject": 1, "marks_obtained": 85, "max_marks": 100},
            ...
        ]
        """
        results_data = request.data
        if not isinstance(results_data, list):
            return Response({"error": "Expected a list of results."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        school_id = getattr(user, 'school_id', None)
        
        created_count = 0
        updated_count = 0
        
        for data in results_data:
            student_id = data.get('student')
            exam_id = data.get('exam')
            subject_id = data.get('subject')
            
            if not all([student_id, exam_id, subject_id]):
                continue
                
            # Ensure max_marks is present
            max_marks = data.get('max_marks', 100)
            marks_obtained = data.get('marks_obtained', 0)

            obj, created = ExamResult.objects.update_or_create(
                student_id=student_id,
                exam_id=exam_id,
                subject_id=subject_id,
                defaults={
                    'marks_obtained': marks_obtained,
                    'max_marks': max_marks,
                    'school_id': school_id
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        return Response({
            "message": f"Successfully processed {created_count + updated_count} results.",
            "created": created_count,
            "updated": updated_count
        })


class LibraryBookViewSet(viewsets.ModelViewSet):
    serializer_class = LibraryBookSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolStaff]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return LibraryBook.objects.all()
        if hasattr(user, 'school_id') and user.school_id:
            return LibraryBook.objects.filter(school_id=user.school_id)
        return LibraryBook.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'school_id') and user.school_id:
            serializer.save(school_id=user.school_id)
        else:
            serializer.save()


class TransportRouteViewSet(viewsets.ModelViewSet):
    serializer_class = TransportRouteSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolStaff]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return TransportRoute.objects.all()
        if hasattr(user, 'school_id') and user.school_id:
            return TransportRoute.objects.filter(school_id=user.school_id)
        return TransportRoute.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'school_id') and user.school_id:
            serializer.save(school_id=user.school_id)
        else:
            serializer.save()


class ReportCardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            student = Student.objects.get(pk=pk)
            exam_results = ExamResult.objects.filter(student=student).select_related('exam', 'subject')
            school_name = (
                getattr(request, 'school', None).name
                if hasattr(request, 'school')
                else "School Management System"
            )
            pdf_buffer = generate_report_card_pdf(
                student=student, exam_results=exam_results, school_name=school_name
            )
            return FileResponse(
                pdf_buffer, as_attachment=True,
                filename=f"report_card_{student.admission_number}.pdf"
            )
        except Student.DoesNotExist:
            return Response({"error": "Student not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeacherAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolStaff]

    def get_queryset(self):
        user = self.request.user
        if not user.school_id:
            return TeacherAssignment.objects.none()
            
        qs = TeacherAssignment.objects.select_related('teacher', 'subject', 'classroom').filter(school_id=user.school_id)
        
        # If user is a teacher, only show their own assignments
        if user.role == 'TEACHER':
            qs = qs.filter(teacher__user=user)
            
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'school_id') and user.school_id:
            serializer.save(school_id=user.school_id)
        else:
            serializer.save()

class SchoolEventViewSet(viewsets.ModelViewSet):
    serializer_class = SchoolEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['event_type', 'target_audience', 'school_id']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return SchoolEvent.objects.all()
            
        if hasattr(user, 'school_id') and user.school_id:
            # All authenticated users belonging to the school can view events
            return SchoolEvent.objects.filter(school_id=user.school_id)
            
        return SchoolEvent.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, 'school_id') and user.school_id:
            serializer.save(school_id=user.school_id)
        else:
            serializer.save()

class GradebookEntryViewSet(viewsets.ModelViewSet):
    serializer_class = GradebookEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['student', 'subject', 'classroom', 'teacher']

    def get_queryset(self):
        user = self.request.user
        if not user.school_id:
            return GradebookEntry.objects.none()
        
        qs = GradebookEntry.objects.filter(school_id=user.school_id)
        
        if user.role == 'TEACHER':
            return qs.filter(teacher__user=user)
        if user.role == 'STUDENT':
            return qs.filter(student__user=user)
        if user.role == 'PARENT':
            return qs.filter(student__parent__user=user)
            
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'TEACHER':
            from teachers.models import Teacher
            teacher = Teacher.objects.get(user=user)
            serializer.save(school_id=user.school_id, teacher=teacher)
        else:
            serializer.save(school_id=user.school_id)


class BulkMarksUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from django.core.files.storage import default_storage
        from .tasks import process_bulk_marks_upload
        
        exam_id = request.data.get('exam_id')
        subject_id = request.data.get('subject_id')
        file_obj = request.FILES.get('file')
        
        if not file_obj or not exam_id or not subject_id:
            return Response({"error": "file, exam_id and subject_id are required."}, status=400)
            
        # Save file temporarily
        file_path = f"tmp/bulk_marks_{request.user.id}_{file_obj.name}"
        path = default_storage.save(file_path, file_obj)
        
        from teachers.models import Teacher
        teacher = Teacher.objects.get(user=request.user) if request.user.role == 'TEACHER' else None

        # Trigger Celery Task
        process_bulk_marks_upload.delay(
            path, 
            request.user.school_id, 
            exam_id, 
            subject_id,
            teacher.id if teacher else None
        )
        
        return Response({"message": "Upload started. It will be processed in the background."}, status=202)

    @action(detail=False, methods=['get'])
    def template(self, request):
        """
        Generates a CSV template for bulk marks upload.
        """
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="marks_template.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['admission_number', 'marks_obtained', 'max_marks'])
        
        # Optionally pre-fill with student admission numbers for a classroom
        classroom_id = request.query_params.get('classroom_id')
        if classroom_id:
            students = Student.objects.filter(classroom_id=classroom_id, school_id=request.user.school_id)
            for s in students:
                writer.writerow([s.admission_number, '', '100'])
                
        return response

class TeacherPerformanceAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from teachers.models import Teacher
        from teachers.services import TeacherAnalyticsService
        
        try:
            teacher = Teacher.objects.get(user=request.user)
        except Teacher.DoesNotExist:
            return Response({"error": "Teacher profile not found."}, status=404)
            
        service = TeacherAnalyticsService()
        
        return Response({
            "overview": service.get_teacher_performance_overview(teacher),
            "distribution": service.get_grade_distribution(teacher),
            "trends": service.get_class_performance_trend(teacher)
        })
