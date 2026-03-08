from rest_framework import serializers
from .models import Teacher, TeacherAttendance, StaffLeave, Payroll


class TeacherSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Teacher
        fields = '__all__'
        read_only_fields = ('school',)

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class TeacherAttendanceSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TeacherAttendance
        fields = '__all__'
        read_only_fields = ('school',)

    def get_teacher_name(self, obj):
        return str(obj.teacher)

class StaffLeaveSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = StaffLeave
        fields = '__all__'
        read_only_fields = ('school', 'status', 'reviewed_on', 'admin_remarks')

    def get_teacher_name(self, obj):
        return f"{obj.teacher.first_name} {obj.teacher.last_name}"

class PayrollSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Payroll
        fields = '__all__'
        read_only_fields = ('school',)

    def get_teacher_name(self, obj):
        return f"{obj.teacher.first_name} {obj.teacher.last_name}"
