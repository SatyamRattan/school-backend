from rest_framework import serializers
from .models import Classroom, Subject, Timetable, Exam, ExamResult, LibraryBook, TransportRoute, TeacherAssignment, SchoolEvent, GradebookEntry


class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = '__all__'
        read_only_fields = ('school',)


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'
        read_only_fields = ('school',)


class TimetableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timetable
        fields = '__all__'
        read_only_fields = ('school',)


class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = '__all__'
        read_only_fields = ('school',)


class ExamResultSerializer(serializers.ModelSerializer):
    # Read-only display fields for context
    student_name = serializers.SerializerMethodField(read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    exam_name = serializers.CharField(source='exam.name', read_only=True)

    class Meta:
        model = ExamResult
        fields = '__all__'
        read_only_fields = ('school',)

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"


class LibraryBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibraryBook
        fields = '__all__'
        read_only_fields = ('school',)


class TransportRouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportRoute
        fields = '__all__'
        read_only_fields = ('school',)


class TeacherAssignmentSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField(read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    classroom_name = serializers.CharField(source='classroom.__str__', read_only=True)

    class Meta:
        model = TeacherAssignment
        fields = '__all__'
        read_only_fields = ('school',)

    def get_teacher_name(self, obj):
        return str(obj.teacher)

class SchoolEventSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    target_audience_display = serializers.CharField(source='get_target_audience_display', read_only=True)

    class Meta:
        model = SchoolEvent
        fields = '__all__'
        read_only_fields = ('school',)

class GradebookEntrySerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.__str__', read_only=True)
    teacher_name = serializers.CharField(source='teacher.__str__', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    classroom_name = serializers.CharField(source='classroom.__str__', read_only=True)

    class Meta:
        model = GradebookEntry
        fields = '__all__'
        read_only_fields = ('school', 'teacher')