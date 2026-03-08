from django.contrib import admin
from .models import StudentRiskRecord

@admin.register(StudentRiskRecord)
class StudentRiskRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'level', 'score', 'last_computed')
    list_filter = ('level', 'school')
    search_fields = ('student__first_name', 'student__last_name', 'student__admission_number')
    readonly_fields = ('last_computed',)
