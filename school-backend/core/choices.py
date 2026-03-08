from django.db import models

class UserRole(models.TextChoices):
    PLATFORM_ADMIN = 'PLATFORM_ADMIN', 'Platform Admin'
    SCHOOL_ADMIN = 'SCHOOL_ADMIN', 'School Admin'
    TEACHER = 'TEACHER', 'Teacher'
    ACCOUNTANT = 'ACCOUNTANT', 'Accountant'
    STUDENT = 'STUDENT', 'Student'
    PARENT = 'PARENT', 'Parent'

class SubscriptionPlan(models.TextChoices):
    MONTHLY = 'MONTHLY', 'Monthly'
    YEARLY = 'YEARLY', 'Yearly'

class SubscriptionStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    INACTIVE = 'INACTIVE', 'Inactive'
    SUSPENDED = 'SUSPENDED', 'Suspended'
    EXPIRED = 'EXPIRED', 'Expired'

class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    SUCCESS = 'SUCCESS', 'Success'
    FAILED = 'FAILED', 'Failed'

class Gender(models.TextChoices):
    MALE = 'M', 'Male'
    FEMALE = 'F', 'Female'
    OTHER = 'O', 'Other'

class AttendanceStatus(models.TextChoices):
    PRESENT = 'PRESENT', 'Present'
    ABSENT = 'ABSENT', 'Absent'
    LEAVE = 'LEAVE', 'Leave'

class StaffAttendanceStatus(models.TextChoices):
    PRESENT = 'PRESENT', 'Present'
    ABSENT = 'ABSENT', 'Absent'
    LATE = 'LATE', 'Late'
    HALF_DAY = 'HALF_DAY', 'Half Day'
    LEAVE = 'LEAVE', 'Leave'

class LeaveStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'

class IncidentType(models.TextChoices):
    GOOD = 'GOOD', 'Good'
    BAD = 'BAD', 'Bad'
    NEUTRAL = 'NEUTRAL', 'Neutral'

class EventType(models.TextChoices):
    HOLIDAY = 'HOLIDAY', 'Holiday'
    EXAM = 'EXAM', 'Exam'
    EXTRA = 'EXTRA', 'Extracurricular'
    OTHER = 'OTHER', 'Other'

class TargetAudience(models.TextChoices):
    ALL = 'ALL', 'All'
    STAFF = 'STAFF', 'Staff Only'
    STUDENT = 'STUDENT', 'Students Only'
    PARENT = 'PARENT', 'Parents'

class RiskLevel(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'
    CRITICAL = 'CRITICAL', 'Critical'

class NotificationType(models.TextChoices):
    FEE_DUE = 'FEE_DUE', 'Fee Due'
    EXAM_RESULT = 'EXAM_RESULT', 'Exam Result'
    GENERAL = 'GENERAL', 'General'

class PaymentMethod(models.TextChoices):
    CASH = 'CASH', 'Cash'
    ONLINE = 'ONLINE', 'Online'
    CHEQUE = 'CHEQUE', 'Cheque'
    BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'

class RazorpayOrderStatus(models.TextChoices):
    CREATED = 'CREATED', 'Created'
    PAID = 'PAID', 'Paid'
    FAILED = 'FAILED', 'Failed'
    EXPIRED = 'EXPIRED', 'Expired'

class PaymentAuditType(models.TextChoices):
    INITIATED = 'INITIATED', 'Initiated'
    WEBHOOK_RECEIVED = 'WEBHOOK_RECEIVED', 'Webhook Received'
    VERIFIED = 'VERIFIED', 'Verified'
    PAYMENT_CREATED = 'PAYMENT_CREATED', 'Payment Record Created'
    FAILED = 'FAILED', 'Failed'
    REFUNDED = 'REFUNDED', 'Refunded'
    SIGNATURE_MISMATCH = 'SIGNATURE_MISMATCH', 'Signature Mismatch'

class PayrollStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PAID = 'PAID', 'Paid'
