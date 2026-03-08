from rest_framework import viewsets, permissions
from .models import StudentRiskRecord
from .serializers import StudentRiskSerializer

class StudentRiskViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows student risk records to be viewed.
    """
    queryset = StudentRiskRecord.objects.all().select_related('student', 'school')
    serializer_class = StudentRiskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # The objects manager is already tenant-aware via TenantManager in core
        # But for analytics, we often want to filter explicitly by school if provided
        school_id = self.request.query_params.get('school_id')
        if school_id:
            return self.queryset.filter(school_id=school_id)
        return self.queryset
