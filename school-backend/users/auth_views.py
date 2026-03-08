from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.throttling import ScopedRateThrottle

class CookieTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh')

            # Set access token cookie
            response.set_cookie(
                key=settings.AUTH_COOKIE,
                value=access_token,
                expires=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE,
                path=settings.AUTH_COOKIE_PATH,
            )

            # Set refresh token cookie
            response.set_cookie(
                key=settings.AUTH_COOKIE_REFRESH,
                value=refresh_token,
                expires=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE,
                path=settings.AUTH_COOKIE_PATH,
            )

            # Set non-HttpOnly cookie for frontend state detection
            response.set_cookie(
                key='logged_in',
                value='true',
                expires=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=False, # Accessible by JS
                samesite=settings.AUTH_COOKIE_SAMESITE,
                path=settings.AUTH_COOKIE_PATH,
            )
            
            # Optional: Remove tokens from response body for maximum security
            # However, keeping them for backward compatibility if needed by other clients
            # delete response.data['access']
            # delete response.data['refresh']

        return response

class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        # Extract refresh token from cookie if not in body
        refresh_token = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)
        if refresh_token and 'refresh' not in request.data:
            request.data['refresh'] = refresh_token

        try:
            response = super().post(request, *args, **kwargs)
        except (InvalidToken, TokenError) as e:
            # If refresh fails (expired/blacklisted), clear cookies
            res = Response({'detail': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
            res.delete_cookie(settings.AUTH_COOKIE)
            res.delete_cookie(settings.AUTH_COOKIE_REFRESH)
            res.delete_cookie('logged_in')
            return res

        if response.status_code == 200:
            access_token = response.data.get('access')
            refresh_token = response.data.get('refresh') # Rotation might provide a new refresh token

            response.set_cookie(
                key=settings.AUTH_COOKIE,
                value=access_token,
                expires=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                samesite=settings.AUTH_COOKIE_SAMESITE,
                path=settings.AUTH_COOKIE_PATH,
            )

            if refresh_token:
                response.set_cookie(
                    key=settings.AUTH_COOKIE_REFRESH,
                    value=refresh_token,
                    expires=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
                    secure=settings.AUTH_COOKIE_SECURE,
                    httponly=settings.AUTH_COOKIE_HTTP_ONLY,
                    samesite=settings.AUTH_COOKIE_SAMESITE,
                    path=settings.AUTH_COOKIE_PATH,
                )
            
            # Update non-HttpOnly cookie
            response.set_cookie(
                key='logged_in',
                value='true',
                expires=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
                secure=settings.AUTH_COOKIE_SECURE,
                httponly=False,
                samesite=settings.AUTH_COOKIE_SAMESITE,
                path=settings.AUTH_COOKIE_PATH,
            )

        return response

class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        response = Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
        response.delete_cookie(settings.AUTH_COOKIE)
        response.delete_cookie(settings.AUTH_COOKIE_REFRESH)
        response.delete_cookie('logged_in')
        
        # Blacklist the refresh token if rotation is on
        refresh_token = request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)
        if refresh_token:
            try:
                from rest_framework_simplejwt.tokens import RefreshToken
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass

        return response
