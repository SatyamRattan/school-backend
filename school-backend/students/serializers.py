from rest_framework import serializers
from .models import Student, Parent, StudentDocument, StudentAttendance, BehaviorReport


class ParentSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Parent
        fields = '__all__'
        read_only_fields = ('school',)

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class StudentDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentDocument
        fields = '__all__'
        read_only_fields = ('school',)


class StudentAttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = StudentAttendance
        fields = '__all__'
        read_only_fields = ('school',)

    def get_student_name(self, obj):
        return str(obj.student)


class StudentSerializer(serializers.ModelSerializer):
    """
    Full student serializer with nested parent details and documents.
    The nested fields are read-only — for write operations use FK IDs.
    """
    parent_details = ParentSerializer(source='parent', read_only=True)
    documents = StudentDocumentSerializer(many=True, read_only=True)
    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Student
        fields = '__all__'
        read_only_fields = ('school',)

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class BehaviorReportSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.__str__', read_only=True)
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    incident_type_display = serializers.CharField(source='get_incident_type_display', read_only=True)

    class Meta:
        model = BehaviorReport
        fields = '__all__'
        read_only_fields = ('school', 'teacher', 'date')
