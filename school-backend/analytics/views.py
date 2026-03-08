from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .services import get_dashboard_stats


class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            school_id = None if user.is_superuser else getattr(user, 'school_id', None)
            stats = get_dashboard_stats(school_id=school_id)
            return Response(stats)
        except Exception as e:
            return Response(
                {"error": f"Analytics unavailable: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
