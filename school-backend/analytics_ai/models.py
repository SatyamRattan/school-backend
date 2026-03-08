from django.db import models
from core.choices import RiskLevel

class StudentRiskRecord(models.Model):

    school = models.ForeignKey('management.School', on_delete=models.CASCADE)
    student = models.OneToOneField('students.Student', on_delete=models.CASCADE, related_name='risk_profile')
    
    score = models.IntegerField() # 0-100
    level = models.CharField(max_length=10, choices=RiskLevel.choices)
    
    # Analysis Components (JSON)
    # { "attendance_trend": -15%, "grade_volatility": "high", "unpaid_fees": 5000 }
    risk_factors = models.JSONField()
    
    # AI Generated Content
    ai_recommendations = models.TextField()
    
    last_computed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} - {self.level} ({self.score})"
