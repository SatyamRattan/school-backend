from django.contrib import admin
from .models import Teacher, TeacherAttendance

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'employee_id', 'email', 'school')
    search_fields = ('first_name', 'last_name', 'employee_id', 'email')
    list_filter = ('school', 'is_active')

@admin.register(TeacherAttendance)
class TeacherAttendanceAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'date', 'status', 'school')
    list_filter = ('status', 'date', 'school')
