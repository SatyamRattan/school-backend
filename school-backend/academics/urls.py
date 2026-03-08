from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClassroomViewSet, SubjectViewSet, TimetableViewSet,
    ExamViewSet, ExamResultViewSet, LibraryBookViewSet,
    TransportRouteViewSet, TeacherAssignmentViewSet, ReportCardView, SchoolEventViewSet,
    GradebookEntryViewSet, BulkMarksUploadView, TeacherPerformanceAnalyticsView
)

router = DefaultRouter()
router.register(r'classrooms', ClassroomViewSet, basename='classroom')
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'timetables', TimetableViewSet, basename='timetable')
router.register(r'exams', ExamViewSet, basename='exam')
router.register(r'exam-results', ExamResultViewSet, basename='exam-result')
router.register(r'library', LibraryBookViewSet, basename='librarybook')
router.register(r'transport', TransportRouteViewSet, basename='transportroute')
router.register(r'teacher-assignments', TeacherAssignmentViewSet, basename='teacherassignment')
router.register(r'events', SchoolEventViewSet, basename='schoolevent')
router.register(r'gradebook', GradebookEntryViewSet, basename='gradebook')

urlpatterns = [
    path('', include(router.urls)),
    path('reports/student/<int:pk>/', ReportCardView.as_view(), name='student-report-card'),
    path('marks/bulk-upload/', BulkMarksUploadView.as_view(), name='bulk-marks-upload'),
    path('teacher/performance/', TeacherPerformanceAnalyticsView.as_view(), name='teacher-performance-analytics'),
]
