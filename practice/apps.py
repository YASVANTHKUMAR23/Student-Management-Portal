from django.apps import AppConfig


class PracticeConfig(AppConfig):

    default_auto_field = "django.db.models.BigAutoField"

    name = "practice"

    def ready(self):

        import practice.signals