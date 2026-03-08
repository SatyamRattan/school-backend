from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False) # Optional for updates

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'phone_number', 'school_id', 'first_name', 'last_name', 'profile_picture', 'password')
        # We allow role/school_id to be written (controlled by ViewSet permission IsSchoolAdmin)
        
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'role', 'phone_number', 'school_id', 'profile_picture')

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
