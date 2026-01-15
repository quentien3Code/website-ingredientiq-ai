from django.apps import AppConfig


class WebsiteConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Website"
    verbose_name = "Website Content (CMS)"
    
    def ready(self):
        """Load signals when app is ready"""
        # Import signals to register them
        from . import signals  # noqa: F401
