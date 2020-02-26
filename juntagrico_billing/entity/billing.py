from django.db import models
from django.utils.translation import gettext as _
from juntagrico.config import Config

from juntagrico.entity import JuntagricoBaseModel
from juntagrico.entity.billing import Billable


class BusinessYear(JuntagricoBaseModel):
    '''
    Business Year for Bills
    '''
    start_date = models.DateField(_('start date'), unique=True)
    name = models.CharField(_('name'), null=True, blank='True', unique=True)

    def __str__(self):
        return self.name or str(self.start_date)

    class Meta:
        verbose_name = _('Business Year')
        verbose_name_plural = _('Business Years')


class Bill(JuntagricoBaseModel):
    '''
    Actuall Bill for billables
    '''
    billable = models.ForeignKey(Billable, related_name='bills',
                                 null=False, blank=False,
                                 on_delete=models.PROTECT,
                                 verbose_name=-('Billable object'))
    business_year = models.ForeignKey('BusinessYear', related_name='bills',
                                      null=False, blank=False,
                                      on_delete=models.PROTECT,
                                      verbose_name=_('Business Year'))
    paid = models.BooleanField(_('paid'), default=False)
    bill_date = models.DateField(
        _('Billing date'), null=True, blank=True)
    ref_number = models.CharField(
        _('Reference number'), max_length=30, unique=True)
    amount = models.FloatField(_('Amount'), null=False, blank=False)
    public_notes = models.TextField(_('Notes visible to {}').format(Config.vocabulary('member_pl')), null=True, blank=True)
    private_notes = models.TextField(_('Notes not visible to {}').format(Config.vocabulary('member_pl')), null=True, blank=True)

    def __str__(self):
        return '{}'.format(self.ref_number)

    class Meta:
        verbose_name = _('Bill')
        verbose_name_plural = _('Bills')


class Payment(JuntagricoBaseModel):
    '''
    Payment for bill
    '''
    bill = models.ForeignKey('Bill', related_name='payments',
                             null=False, blank=False,
                             on_delete=models.PROTECT, verbose_name=_('Bill'))
    paid_date = models.DateField(_('Paid date'), null=True, blank=True)
    amount = models.FloatField(_('Amount number'), null=False, blank=False)
    private_notes = models.TextField(_('Notes not visible to {}').format(Config.vocabulary('member_pl')), null=True, blank=True)

    def __str__(self):
        return '{}'.format(self.bill.ref_number)

    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payment')
