from django.apps import AppConfig


class JuntagricoAppconfig(AppConfig):
    name = "juntagrico_billing"
    default_auto_field = 'django.db.models.AutoField'

    def ready(self):
        from juntagrico.util import addons
        addons.config.register_version(self.name)

        from juntagrico_billing.config import Config
        addons.config.register_config_class(Config)
