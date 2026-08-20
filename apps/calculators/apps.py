from django.apps import AppConfig


class CalculatorsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.calculators"
    verbose_name = "Будівельні калькулятори"

    def ready(self):
        # Автоматична реєстрація всіх калькуляторів при запуску Django
        from apps.calculators.engine.registry import register_all_calculators
        register_all_calculators()
