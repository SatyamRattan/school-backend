from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.throttling import ScopedRateThrottle
from .models import User
from .serializers import UserSerializer, UserRegistrationSerializer

from core.permissions import IsSchoolAdmin

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolAdmin]

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.all()
        
        # Superuser sees all
        if user.is_superuser:
            pass
        # School Admin/Teacher/Student sees only their school
        elif user.school_id:
            queryset = queryset.filter(school_id=user.school_id)
        else:
            return User.objects.none()

        # Filter by role if provided
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
            
        return queryset

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegistrationSerializer

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
