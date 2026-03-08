from django.db import models
from students.models import Student
from teachers.models import Teacher
from management.models import School
from core.choices import EventType, TargetAudience

class Classroom(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='classrooms', null=True) # Check null=True for migration compatibility
    name = models.CharField(max_length=50) # e.g., '10th', '12th'
    section = models.CharField(max_length=10) # e.g., 'A', 'B'
    class_teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='managed_classes')

    def __str__(self):
        return f"{self.name} - {self.section}"

    class Meta:
        unique_together = ('school', 'name', 'section')
        verbose_name_plural = "Classrooms"

class Subject(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='subjects', null=True)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('school', 'code')

class Timetable(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='timetables', null=True)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='timetables')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    day_of_week = models.IntegerField() # 0-6
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.classroom} - {self.subject} ({self.day_of_week})"

    class Meta:
        unique_together = ('classroom', 'day_of_week', 'start_time')

class Exam(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='exams', null=True)
    name = models.CharField(max_length=100) # e.g., 'Half Yearly', 'Finals'
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('school', 'name')

class ExamResult(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='exam_results', null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    max_marks = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.student} - {self.exam} - {self.subject}"

    class Meta:
        unique_together = ('student', 'exam', 'subject')

# --- Library Management ---
class LibraryBook(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='library_books', null=True)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return self.title

    class Meta:
        unique_together = ('school', 'title', 'author')

# --- Transport Management ---
class TransportRoute(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='transport_routes', null=True)
    route_name = models.CharField(max_length=100)
    vehicle_number = models.CharField(max_length=20)
    driver_name = models.CharField(max_length=100)
    driver_phone = models.CharField(max_length=15)

    def __str__(self):
        return self.route_name

    class Meta:
        unique_together = ('school', 'route_name')

# --- Teacher Assignment (links teacher → subject in a specific classroom) ---
class TeacherAssignment(models.Model):
    """
    Assigns a teacher to teach a specific subject in a specific classroom.
    Used by timetable scheduling and academic reporting.
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='teacher_assignments', null=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='assignments')
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='teacher_assignments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='teacher_assignments')

    def __str__(self):
        return f"{self.teacher} → {self.subject.name} ({self.classroom})"

    class Meta:
        unique_together = ('teacher', 'classroom', 'subject')

class SchoolEvent(models.Model):
    """
    Centralized calendar system for scheduling and tracking school events.
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='events', null=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    event_type = models.CharField(max_length=20, choices=EventType.choices, default=EventType.OTHER)
    target_audience = models.CharField(max_length=20, choices=TargetAudience.choices, default=TargetAudience.ALL)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.title} ({self.get_event_type_display()})"

class GradebookEntry(models.Model):
    """
    Granular tracking for class tests, assignments, and quizzes.
    Feeds into the overall academic analytics.
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='gradebook_entries', null=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='gradebook_entries')
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='gradebook_entries')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='gradebook_entries')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='gradebook_entries')
    
    title = models.CharField(max_length=200) # e.g., "Term 1 Quiz"
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    max_marks = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['teacher', 'subject', 'classroom']),
            models.Index(fields=['student', 'subject']),
        ]
        verbose_name_plural = "Gradebook Entries"

    def __str__(self):
        return f"{self.student} - {self.title} ({self.marks_obtained}/{self.max_marks})"
