from django.apps import AppConfig


class GroupManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'group_manager'
    def ready(self):
        # Cargar las signals
        import group_manager.signals 
        