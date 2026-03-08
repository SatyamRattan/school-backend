from django.contrib.auth.models import AbstractUser
from django.db import models

from core.models import TenantUserManager
from core.choices import UserRole

def upload_user_profile_picture(instance, filename):
    return f'profile_pictures/{instance.username}/{filename}'

class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.STUDENT
    )
    
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    
    # Identify which school this user belongs to in the central DB
    # For Super Admin, this will be null
    school_id = models.IntegerField(null=True, blank=True)
    
    profile_picture = models.ImageField(upload_to=upload_user_profile_picture, null=True, blank=True)

    objects = TenantUserManager()

    def __str__(self):
        return f"{self.username} ({self.role})"

    

    
