from django.db import models
from django.utils.translation import gettext as _

from juntagrico.entity import JuntagricoBaseModel
from juntagrico.entity.billing import Billable


class Bill(JuntagricoBaseModel):
    '''
    Actuall Bill for billables
    '''
    billable = models.ForeignKey(Billable, related_name='bills',
                                 null=False, blank=False,
                                 on_delete=models.PROTECT)
    paid = models.BooleanField(_('bezahlt'), default=False)
    bill_date = models.DateField(
        _('Aktivierungssdatum'), null=True, blank=True)
    ref_number = models.CharField(
        _('Referenznummer'), max_length=30, unique=True)
    amount = models.FloatField(_('Betrag'), null=False, blank=False)

    def __str__(self):
        return '%s' % self.ref_number

    class Meta:
        verbose_name = _('Rechnung')
        verbose_name_plural = _('Rechnungen')


class Payment(JuntagricoBaseModel):
    '''
    Payment for bill
    '''
    bill = models.ForeignKey('Bill', related_name='payments',
                             null=False, blank=False,
                             on_delete=models.PROTECT)
    paid_date = models.DateField(_('Bezahldatum'), null=True, blank=True)
    amount = models.FloatField(_('Betrag'), null=False, blank=False)

    def __str__(self):
        return '%s' % self.ref_number

    class Meta:
        verbose_name = _('Zahlung')
        verbose_name_plural = _('Zahlungen')
