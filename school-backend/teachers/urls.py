from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TeacherViewSet, TeacherAttendanceViewSet, StaffLeaveViewSet, PayrollViewSet

router = DefaultRouter()
router.register(r'staff', TeacherViewSet, basename='teacher')
router.register(r'attendance', TeacherAttendanceViewSet, basename='teacher-attendance')
router.register(r'leaves', StaffLeaveViewSet, basename='teacher-leave')
router.register(r'payroll', PayrollViewSet, basename='teacher-payroll')

urlpatterns = [
    path('', include(router.urls)),
]
