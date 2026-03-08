from django.contrib import admin
from .models import Classroom, Subject, Timetable, Exam, ExamResult, LibraryBook, TransportRoute, GradebookEntry

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'section', 'class_teacher', 'school')
    list_filter = ('school',)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'school')
    list_filter = ('school',)

@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('classroom', 'subject', 'teacher', 'day_of_week', 'school')
    list_filter = ('school', 'day_of_week')

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'school')
    list_filter = ('school',)

@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'subject', 'marks_obtained', 'max_marks', 'school')
    list_filter = ('school', 'exam', 'subject')

@admin.register(LibraryBook)
class LibraryBookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'quantity', 'school')
    list_filter = ('school',)

@admin.register(TransportRoute)
class TransportRouteAdmin(admin.ModelAdmin):
    list_display = ('route_name', 'vehicle_number', 'driver_name', 'school')
    list_filter = ('school',)

@admin.register(GradebookEntry)
class GradebookEntryAdmin(admin.ModelAdmin):
    list_display = ('student', 'title', 'subject', 'marks_obtained', 'teacher', 'school')
    list_filter = ('school', 'teacher', 'subject', 'classroom')
    search_fields = ('student__first_name', 'student__last_name', 'title')
