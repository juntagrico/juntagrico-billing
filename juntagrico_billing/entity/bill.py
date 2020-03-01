from datetime import date
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
    name = models.CharField(_('name'), max_length=20, null=True, blank='True', unique=True)

    # derived properties
    @property
    def end_date(self):
        # at the moment always the end of year
        if self.start_date:
            return date(self.start_date.year, 12, 31)
        else:
            return None
        

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
                                 verbose_name=_('Billable object'))
    business_year = models.ForeignKey('BusinessYear', related_name='bills',
                                      null=False, blank=False,
                                      on_delete=models.PROTECT,
                                      verbose_name=_('Business Year'))
    exported = models.BooleanField(_('exported'), default=False)
    bill_date = models.DateField(
        _('Billing date'), null=True, blank=True)
    amount = models.FloatField(_('Amount'), null=False, blank=False)
    paid = models.BooleanField(_('bezahlt'), default=False)
    public_notes = models.TextField(_('Notes visible to {}').format(Config.vocabulary('member_pl')), null=True, blank=True)
    private_notes = models.TextField(_('Notes not visible to {}').format(Config.vocabulary('member_pl')), null=True, blank=True)

    # derived properties
    @property
    def member_name(self):
        if self.billable:
            return self.billable.primary_member_nullsave()
        return ""


    def __str__(self):
        return '{}'.format(self.id)

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
        return '{}'.format(self.bill.id)

    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payment')
