from asgiref.local import Local

_thread_locals = Local()

def set_tenant_db(db_name, school_id=None):
    _thread_locals.tenant_db = db_name
    if school_id:
        _thread_locals.school_id = school_id

def get_tenant_db():
    return getattr(_thread_locals, 'tenant_db', 'default')

def get_current_school_id():
    return getattr(_thread_locals, 'school_id', None)

def clear_tenant_db():
    if hasattr(_thread_locals, 'tenant_db'):
        del _thread_locals.tenant_db
    if hasattr(_thread_locals, 'school_id'):
        del _thread_locals.school_id

class TenantRouter:
    CENTRAL_APPS = ['management', 'users', 'admin', 'contenttypes', 'sessions', 'messages', 'notifications', 'auth', 'django_celery_beat', 'token_blacklist']

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.CENTRAL_APPS:
            return 'default'
        return get_tenant_db()

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.CENTRAL_APPS:
            return 'default'
        return get_tenant_db()

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._state.db == obj2._state.db:
            return True
        # Allow relations between central apps (management, users) and others
        central_apps = ['management', 'users']
        if obj1._meta.app_label in central_apps or obj2._meta.app_label in central_apps:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Central apps only migrate to 'default'
        if app_label in self.CENTRAL_APPS:
            return db == 'default'
        
        # Tenant apps can migrate to 'default' in development,
        # but should always be allowed on tenant databases.
        if db == 'default':
            return True
            
        # On tenant databases, ONLY allow tenant apps
        return app_label not in self.CENTRAL_APPS
