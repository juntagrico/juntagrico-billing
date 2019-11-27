from django.db import models

class Settings(models.Model):
    """
    Singleton Settings object for bookkeeping.
    """
    class Meta:
        verbose_name_plural = "Settings"

    debtor_account = models.CharField('Debitor-Konto', max_length=10)
    
    def save(self, *args, **kwargs):
        # make sure there is only 1 instance of settings
        self.id=1
        super(Settings, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # don't allow deletion
        pass
