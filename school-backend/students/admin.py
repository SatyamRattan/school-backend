from django.contrib import admin
from .models import Parent, Student, StudentDocument, StudentAttendance

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone_number', 'school')
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('school',)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'admission_number', 'classroom', 'parent', 'school')
    search_fields = ('first_name', 'last_name', 'admission_number')
    list_filter = ('school', 'classroom', 'gender', 'is_active')

@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ('student', 'title', 'uploaded_at', 'school')
    list_filter = ('school',)

@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status', 'school')
    list_filter = ('status', 'date', 'school')
