from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet, ParentViewSet, StudentDocumentViewSet, BulkStudentImportView, StudentAttendanceViewSet

router = DefaultRouter()
router.register(r'records', StudentViewSet, basename='student')
router.register(r'parents', ParentViewSet, basename='parent')
router.register(r'documents', StudentDocumentViewSet, basename='student-document')
router.register(r'attendance', StudentAttendanceViewSet, basename='student-attendance')

urlpatterns = [
    path('upload-csv/', BulkStudentImportView.as_view(), name='student-bulk-import'),
    path('', include(router.urls)),
]
