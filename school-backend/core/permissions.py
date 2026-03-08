from rest_framework import permissions

class IsSchoolStaff(permissions.BasePermission):
    """
    Allocates write access to School Admins and Teachers only.
    Read access is allowed to authenticated users (including students/parents) if the view allows it.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Helper to check role
        def is_staff(user):
            if user.is_superuser:
                return True
            return user.role in ['SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER']

        # Allow safe methods (GET, HEAD, OPTIONS) for authenticated users (handled by IsAuthenticated usually)
        # But here we enforce staff for unsafe methods
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return is_staff(request.user)

class IsStudentOrParent(permissions.BasePermission):
    """
    Read-only access for Students and Parents.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['STUDENT', 'PARENT']

class IsSchoolAdmin(permissions.BasePermission):
    """
    Allocates write access only to School Admins (and Super Admins).
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_superuser or request.user.role == 'SCHOOL_ADMIN'

class IsFinanceStaff(permissions.BasePermission):
    """
    Allocates write access to School Admins and Accountants.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_superuser or request.user.role in ['SCHOOL_ADMIN', 'ACCOUNTANT']
