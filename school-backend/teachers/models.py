from django.db import models
from management.models import School
from core.choices import StaffAttendanceStatus, LeaveStatus, PayrollStatus

class Teacher(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='teachers', null=True)
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, null=True, blank=True, related_name='teacher_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=50)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    qualification = models.CharField(max_length=255)
    date_of_joining = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"

    class Meta:
        unique_together = (('school', 'employee_id'), ('school', 'email'))

class TeacherAttendance(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='teacher_attendance_records', null=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=StaffAttendanceStatus.choices)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('teacher', 'date')

    def __str__(self):
        return f"{self.teacher} - {self.date} - {self.status}"

class StaffLeave(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='staff_leaves', null=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='leaves')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=LeaveStatus.choices, default=LeaveStatus.PENDING)
    applied_on = models.DateTimeField(auto_now_add=True)
    reviewed_on = models.DateTimeField(null=True, blank=True)
    admin_remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-applied_on']

    def __str__(self):
        return f"{self.teacher} ({self.start_date} to {self.end_date}) - {self.status}"

class Payroll(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='payrolls', null=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='payrolls')
    month = models.DateField(help_text="The month and year for this payroll (e.g., set to 1st of the month)")
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_payable = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PayrollStatus.choices, default=PayrollStatus.PENDING)
    paid_on = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('teacher', 'month')
        ordering = ['-month']

    def __str__(self):
        return f"{self.teacher} - {self.month.strftime('%b %Y')} - {self.status}"
