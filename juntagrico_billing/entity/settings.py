from django.db import models
from django.utils.translation import gettext as _


class Settings(models.Model):
    """
    Singleton Settings object for bookkeeping.
    """
    class Meta:
        verbose_name_plural = "Settings"

    debtor_account = models.CharField('Debitor-Konto', max_length=10)
    default_paymenttype = models.ForeignKey('PaymentType', null=True,
                                            on_delete=models.SET_NULL)

    vat_number = models.CharField(_('VAT Number'), max_length=20, null=True, blank=True)
    vat_percent = models.FloatField(_('VAT Percent'), null=False, blank=False, default=0.0)

    def save(self, *args, **kwargs):
        # make sure there is only 1 instance of settings
        self.id = 1
        super(Settings, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # don't allow deletion
        pass
