from django.db import models
from .db_router import get_current_school_id

class TenantQuerySet(models.QuerySet):
    def filter_by_tenant(self):
        school_id = get_current_school_id()
        if school_id:
            # Use field inspection to determine the correct filter
            opts = self.model._meta
            if any(f.name == 'school_id' for f in opts.fields):
                return self.filter(school_id=school_id)
            elif any(f.name == 'school' for f in opts.fields):
                return self.filter(school_id=school_id)
        return self

class TenantManager(models.Manager):
    def get_queryset(self):
        # Automatically scope all queries if a school context is present
        return TenantQuerySet(self.model, using=self._db).filter_by_tenant()

    def get_by_natural_key(self, username):
        return self.get_queryset().get(**{self.model.USERNAME_FIELD: username})

from django.contrib.auth.models import UserManager

class TenantUserManager(UserManager):
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db).filter_by_tenant()

class TenantModelMixin(models.Model):
    """
    Mixin to provide automatic tenant scoping via TenantManager.
    """
    class Meta:
        abstract = True
    
    # To be applied to models where you want 'objects' to be tenant-aware by default
    # objects = TenantManager()
