from django.test import TestCase
from management.models import School
from students.models import Student
from core.db_router import TenantRouter, set_tenant_db, clear_tenant_db

class DatabaseRouterTest(TestCase):
    def setUp(self):
        self.router = TenantRouter()

    def test_central_apps_routing(self):
        """Management models should always route to 'default'."""
        school = School(name="Central School")
        self.assertEqual(self.router.db_for_read(School), 'default')
        self.assertEqual(self.router.db_for_write(School), 'default')

    def test_tenant_apps_routing_default(self):
        """By default, tenant models should route to 'default' (or current thread local)."""
        clear_tenant_db()
        self.assertEqual(self.router.db_for_read(Student), 'default')

    def test_tenant_apps_routing_specific(self):
        """When a tenant is set in thread locals, student model should route there."""
        set_tenant_db('tenant_alpha')
        self.assertEqual(self.router.db_for_read(Student), 'tenant_alpha')
        clear_tenant_db()

    def test_allow_relation(self):
        """Relations between management and other apps should be allowed."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User(username="admin")
        school = School(name="Test")
        # Relations involving 'management' or 'users' are allowed
        self.assertTrue(self.router.allow_relation(user, school))
