from django.db import models
from management.models import School
from core.choices import Gender, AttendanceStatus, IncidentType

class Parent(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='parents', null=True)
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='parent_profile', null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    address = models.TextField()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        unique_together = ('school', 'email')

class Student(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='students_at_school', null=True) # Changed related_name to avoid clash with Parent.students
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='student_profile', null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    admission_number = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='students')
    classroom = models.ForeignKey('academics.Classroom', on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    
    gender = models.CharField(max_length=1, choices=Gender.choices)
    
    joining_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.admission_number})"

    class Meta:
        unique_together = ('school', 'admission_number')

class StudentDocument(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='student_documents', null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='student_docs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class StudentAttendance(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='student_attendance_records', null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=AttendanceStatus.choices)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('student', 'date')

    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"

class BehaviorReport(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='behavior_reports', null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='behavior_reports')
    teacher = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='logged_behaviors')
    incident_type = models.CharField(max_length=10, choices=IncidentType.choices, default=IncidentType.NEUTRAL)
    comment = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.student} - {self.incident_type} on {self.date.date()}"
