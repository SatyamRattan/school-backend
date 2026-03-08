from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.conf import settings
from datetime import date, timedelta
import razorpay

from .models import (
    School, CustomDomain, Subscription, TenantDatabase,
    PaymentTransaction
)
from .serializers import (
    SchoolSerializer, CustomDomainSerializer, 
    SubscriptionSerializer, TenantDatabaseSerializer,
    PaymentInitiateSerializer, PaymentVerifySerializer
)

class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_permissions(self):
        if self.action in ['create', 'register_tenant']:
            return [permissions.AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=['post'])
    def register_tenant(self, request):
        from .serializers import TenantRegistrationSerializer
        from django.contrib.auth import get_user_model
        from datetime import date, timedelta
        
        User = get_user_model()
        
        serializer = TenantRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            try:
                with transaction.atomic():
                    # 1. Create School
                    school = School.objects.create(
                        name=data['school_name'],
                        code=data['subdomain']
                    )
                    
                    # 2. Create User (School Admin)
                    user = User.objects.create_user(
                        username=data['admin_email'].split('@')[0] + f"_{school.code}", # Unique username
                        email=data['admin_email'],
                        password=data['password'],
                        role='SCHOOL_ADMIN',
                        school_id=school.id,
                        first_name=data.get('admin_name', 'Admin').split(' ')[0],
                        last_name=data.get('admin_name', 'User').split(' ')[-1] if ' ' in data.get('admin_name', '') else ''
                    )
                    
                    # 3. Create Subscription (Trial/Active)
                    Subscription.objects.create(
                        school=school,
                        plan='MONTHLY',
                        start_date=date.today(),
                        expiry_date=date.today() + timedelta(days=14), # 14 Day Trial
                        status='ACTIVE'
                    )
                    
                    # 4. Create Tenant Database Record
                    TenantDatabase.objects.create(
                        school=school,
                        db_name=f"sms_{school.code}"
                    )
                    
                    # 5. Create Custom Domain
                    CustomDomain.objects.create(
                        school=school,
                        domain=f"{school.code}.sms.com",
                        is_primary=True
                    )
                    
                    return Response({
                        "message": "School registered successfully.",
                        "school_id": school.id,
                        "school_code": school.code,
                        "admin_email": user.email
                    }, status=status.HTTP_201_CREATED)
                    
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomDomainViewSet(viewsets.ModelViewSet):
    queryset = CustomDomain.objects.all()
    serializer_class = CustomDomainSerializer
    permission_classes = [permissions.IsAdminUser]

class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAdminUser]

class TenantDatabaseViewSet(viewsets.ModelViewSet):
    queryset = TenantDatabase.objects.all()
    serializer_class = TenantDatabaseSerializer
    permission_classes = [permissions.IsAdminUser]

class PaymentViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def initiate(self, request):
        serializer = PaymentInitiateSerializer(data=request.data)
        if serializer.is_valid():
            # In a real scenario, get the school from the logged-in user's context
            # For now, we assume the user is a School Admin linked to a school
            user = request.user
            if user.role != 'SCHOOL_ADMIN' or not user.school_id:
                return Response({"error": "Only School Admins can initiate payments."}, status=status.HTTP_403_FORBIDDEN)
            
            try:
                school = School.objects.get(id=user.school_id)
            except School.DoesNotExist:
                return Response({"error": "School not found."}, status=status.HTTP_404_NOT_FOUND)

            plan = serializer.validated_data['plan']
            amount = 1000 if plan == 'MONTHLY' else 10000 # Example pricing
            currency = serializer.validated_data['currency']

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            data = { "amount": amount * 100, "currency": currency, "receipt": f"receipt_{school.code}_{date.today()}" }
            payment_order = client.order.create(data=data)

            # Create Transaction Record
            PaymentTransaction.objects.create(
                school=school,
                order_id=payment_order['id'],
                amount=amount,
                currency=currency,
                status='PENDING'
            )

            return Response(payment_order)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def verify(self, request):
        serializer = PaymentVerifySerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            try:
                client.utility.verify_payment_signature(data)
            except razorpay.errors.SignatureVerificationError:
                return Response({"error": "Invalid Signature"}, status=status.HTTP_400_BAD_REQUEST)

            # Update Transaction
            try:
                transaction = PaymentTransaction.objects.get(order_id=data['razorpay_order_id'])
                transaction.payment_id = data['razorpay_payment_id']
                transaction.status = 'SUCCESS'
                transaction.save()
                
                # Update Subscription
                school = transaction.school
                subscription = school.subscription
                
                # Logic to extend subscription
                current_expiry = subscription.expiry_date
                if current_expiry < date.today():
                    current_expiry = date.today() # Reset if already expired
                
                # Extend based on Amount/Plan (Simplified Logic)
                # Ideally, we should store the plan in the transaction or pass it here
                days_to_add = 30 if transaction.amount == 1000 else 365
                subscription.expiry_date = current_expiry + timedelta(days=days_to_add)
                subscription.status = 'ACTIVE'
                subscription.save()
                
                return Response({"status": "Payment Successful", "new_expiry": subscription.expiry_date})
            
            except PaymentTransaction.DoesNotExist:
                return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
