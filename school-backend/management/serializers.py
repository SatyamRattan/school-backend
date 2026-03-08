from rest_framework import serializers
from .models import School, Subscription, CustomDomain, TenantDatabase, PaymentTransaction
from core.choices import SubscriptionPlan
from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()

class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = '__all__'

class CustomDomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomDomain
        fields = '__all__'

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'

class TenantDatabaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantDatabase
        fields = '__all__'

class TenantRegistrationSerializer(serializers.Serializer):
    school_name = serializers.CharField(max_length=255)
    subdomain = serializers.SlugField()
    admin_email = serializers.EmailField()
    admin_name = serializers.CharField(max_length=150, required=False) # Optional
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_subdomain(self, value):
        if CustomDomain.objects.filter(domain__istartswith=f"{value}.").exists():
             # roughly check if something starting with this subdomain exists, 
             # better exact check:
             pass 
        # Actually, let's assume domain is value + .sms.com for now
        # But CustomDomain stores full domain. 
        # Let's just check School code uniqueness for now as code ~ subdomain
        if School.objects.filter(code=value).exists():
            raise serializers.ValidationError("This subdomain/code is already taken.")
        return value

    def validate_admin_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value

class PaymentInitiateSerializer(serializers.Serializer):
    plan = serializers.ChoiceField(choices=SubscriptionPlan.choices)
    currency = serializers.CharField(max_length=3, default='INR')

class PaymentVerifySerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()
