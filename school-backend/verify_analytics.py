import os
import django
import sys
import json

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from analytics.views import DashboardView
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model

User = get_user_model()

def verify_analytics():
    print("📊 Verifying Analytics Dashboard (Mocked DB)...")
    
    factory = APIRequestFactory()
    request = factory.get('/api/analytics/dashboard/')
    
    # Mock User
    user = User(username='admin', email='admin@example.com', is_active=True, is_superuser=True)
    force_authenticate(request, user=user)
    
    view = DashboardView.as_view()
    
    # Mock the service call
    with patch('analytics.views.get_dashboard_stats') as mock_stats:
        mock_stats.return_value = {
            'counts': {'students': 100, 'teachers': 10},
            'finance': {'total_revenue': 50000, 'monthly_revenue': 5000},
            'activity': [{'student': 'John', 'amount': 1000}],
            'charts': {'attendance': {'labels': [], 'data': []}}
        }
        
        try:
            response = view(request)
            if response.status_code == 200:
                print("✅ Dashboard API successful (200 OK)")
                print(json.dumps(response.data, indent=2))
            else:
                print(f"❌ API failed: {response.status_code} - {response.data}")
                
        except Exception as e:
            print(f"❌ Exception during view execution: {e}")

if __name__ == "__main__":
    verify_analytics()
