from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import CustomDomain, School, TenantDatabase

@receiver([post_save, post_delete], sender=CustomDomain)
def invalidate_domain_cache(sender, instance, **kwargs):
    cache.delete(f"tenant_domain_{instance.domain}")

@receiver([post_save, post_delete], sender=School)
def invalidate_school_domains_cache(sender, instance, **kwargs):
    for domain in instance.domains.all():
        cache.delete(f"tenant_domain_{domain.domain}")

@receiver([post_save, post_delete], sender=TenantDatabase)
def invalidate_db_domains_cache(sender, instance, **kwargs):
    for domain in instance.school.domains.all():
        cache.delete(f"tenant_domain_{domain.domain}")
