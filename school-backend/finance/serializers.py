from rest_framework import serializers
from .models import FeeType, FeeStructure, FeePayment, RazorpayOrder, LateFine, FeeReceipt


class FeeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeType
        fields = '__all__'
        read_only_fields = ('school',)


class FeeStructureSerializer(serializers.ModelSerializer):
    fee_type_name = serializers.CharField(source='fee_type.name', read_only=True)
    classroom_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FeeStructure
        fields = '__all__'
        read_only_fields = ('school',)

    def get_classroom_name(self, obj):
        return str(obj.classroom) if obj.classroom else None


class FeePaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField(read_only=True)
    fee_type_name = serializers.CharField(source='fee_structure.fee_type.name', read_only=True)

    class Meta:
        model = FeePayment
        fields = '__all__'
        read_only_fields = ('school',)

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"


class RazorpayOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = RazorpayOrder
        fields = [
            'id', 'razorpay_order_id', 'amount', 'currency',
            'status', 'created_at', 'paid_at', 'idempotency_key'
        ]
        read_only_fields = fields


class LateFineSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.__str__', read_only=True)
    fee_type_name = serializers.CharField(source='fee_structure.fee_type.name', read_only=True)

    class Meta:
        model = LateFine
        fields = '__all__'
        read_only_fields = ('school',)


class FeeReceiptSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='fee_payment.student.__str__', read_only=True)
    amount_paid = serializers.DecimalField(
        source='fee_payment.amount_paid', max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = FeeReceipt
        fields = ['id', 'receipt_number', 'generated_at', 'pdf_file', 'student_name', 'amount_paid', 'school']
        read_only_fields = fields