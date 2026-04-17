from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    # 🔗 Load signals when app is ready
    def ready(self):
        import accounts.signals
        