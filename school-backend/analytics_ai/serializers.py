from rest_framework import serializers
from .models import StudentRiskRecord

class StudentRiskSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.__str__', read_only=True)
    
    class Meta:
        model = StudentRiskRecord
        fields = [
            'id', 'student', 'student_name', 'score', 'level', 
            'risk_factors', 'ai_recommendations', 'last_computed'
        ]
