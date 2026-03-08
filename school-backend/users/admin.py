from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Fields', {'fields': ('role', 'phone_number', 'school_id', 'profile_picture')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Extra Fields', {'fields': ('role', 'phone_number', 'school_id', 'profile_picture')}),
    )
    list_display = ('username', 'email', 'role', 'school_id', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')
