from django.conf import settings
from .db_router import set_tenant_db, clear_tenant_db
from management.models import CustomDomain, TenantDatabase, School
from django.http import HttpResponseForbidden

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0] # Remove port if present
        
        from django.core.cache import cache
        cache_key = f"tenant_domain_{host}"
        domain_data = cache.get(cache_key)

        if domain_data:
            school_id = domain_data['school_id']
            tenant_db = domain_data['db_name']
            is_active = domain_data['is_active']
            
            if not is_active:
                return HttpResponseForbidden("School is suspended.")
            
            # Fetch school object (fast PK lookup)
            try:
                school = School.objects.get(id=school_id)
            except School.DoesNotExist:
                cache.delete(cache_key)
                return self.get_response(request)
        else:
            # Check if this is a known domain
            try:
                domain_obj = CustomDomain.objects.select_related('school', 'school__database').get(domain=host)
                school = domain_obj.school
                
                if not school.is_active:
                    return HttpResponseForbidden("School is suspended due to non-payment or admin action.")
                
                tenant_db = school.database.db_name
                
                # Cache the results
                cache.set(cache_key, {
                    'school_id': school.id,
                    'db_name': tenant_db,
                    'is_active': school.is_active
                }, timeout=settings.DOMAIN_CACHE_TIMEOUT)
                
            except CustomDomain.DoesNotExist:
                clear_tenant_db()
                request.school = None
                return self.get_response(request)

        # Common logic for both cache hit/miss
        if tenant_db not in settings.DATABASES:
            new_db_config = settings.DATABASES['default'].copy()
            new_db_config.update({
                'NAME': tenant_db,
                'USER': settings.TENANT_DB_USER,
                'PASSWORD': settings.TENANT_DB_PASSWORD,
                'HOST': settings.TENANT_DB_HOST,
                'PORT': settings.TENANT_DB_PORT,
            })
            settings.DATABASES[tenant_db] = new_db_config
        
        set_tenant_db(tenant_db, school.id)
        request.school = school

        response = self.get_response(request)
        
        # Clean up after request
        clear_tenant_db()
        
        return response
