from django.contrib import admin
from .models import (
    FeeType, FeeStructure, FeePayment,
    RazorpayOrder, PaymentAuditLog, LateFine, FeeReceipt
)

@admin.register(FeeType)
class FeeTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'school')
    list_filter = ('school',)

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('fee_type', 'classroom', 'amount', 'due_date', 'late_fine_per_day', 'school')
    list_filter = ('school', 'academic_year')

@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'fee_structure', 'amount_paid', 'payment_date', 'payment_method', 'school')
    list_filter = ('school', 'payment_method', 'payment_date')
    search_fields = ('student__first_name', 'student__last_name', 'transaction_id')

@admin.register(RazorpayOrder)
class RazorpayOrderAdmin(admin.ModelAdmin):
    list_display = ('razorpay_order_id', 'student', 'amount', 'status', 'created_at', 'paid_at')
    list_filter = ('status', 'school')
    search_fields = ('razorpay_order_id', 'razorpay_payment_id', 'student__first_name')
    readonly_fields = ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'idempotency_key')

@admin.register(PaymentAuditLog)
class PaymentAuditLogAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'razorpay_order', 'razorpay_payment_id', 'ip_address', 'created_at')
    list_filter = ('event_type',)
    readonly_fields = ('razorpay_order', 'event_type', 'razorpay_payment_id', 'payload_json', 'ip_address', 'created_at')

    def has_change_permission(self, request, obj=None):
        return False  # Immutable audit log

    def has_delete_permission(self, request, obj=None):
        return False  # Immutable audit log

@admin.register(LateFine)
class LateFineAdmin(admin.ModelAdmin):
    list_display = ('student', 'fee_structure', 'fine_amount', 'days_overdue', 'is_waived', 'school')
    list_filter = ('school', 'is_waived')
    search_fields = ('student__first_name', 'student__last_name')
    actions = ['waive_selected_fines']

    def waive_selected_fines(self, request, queryset):
        queryset.update(is_waived=True, waived_by=request.user)
    waive_selected_fines.short_description = "Waive selected late fines"

@admin.register(FeeReceipt)
class FeeReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'fee_payment', 'generated_at', 'school')
    list_filter = ('school',)
    readonly_fields = ('receipt_number', 'generated_at')
