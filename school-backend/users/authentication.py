from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import CSRFCheck
from rest_framework import exceptions

class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom authentication class that extends JWTAuthentication to support
    tokens stored in cookies, in addition to the standard Authorization header.
    """
    def authenticate(self, request):
        header = self.get_header(request)
        
        if header is None:
            # Fallback to cookie if header is not present
            raw_token = request.COOKIES.get(settings.AUTH_COOKIE)
        else:
            raw_token = self.get_raw_token(header)

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)

        # Enforce CSRF check if the token was retrieved from a cookie
        if header is None:
            self.enforce_csrf(request)

        return self.get_user(validated_token), validated_token

    def enforce_csrf(self, request):
        """
        Enforce CSRF protection for cookie-based authentication.
        """
        check = CSRFCheck(lambda r: None) # Dummy view
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            raise exceptions.PermissionDenied(f'CSRF Failed: {reason}')
