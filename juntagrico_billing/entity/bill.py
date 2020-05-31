from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext as _
from juntagrico.config import Config
from juntagrico.entity import JuntagricoBaseModel
from juntagrico.entity.billing import Billable
from juntagrico.entity.extrasubs import ExtraSubscription
from juntagrico.entity.subs import Subscription

from juntagrico_billing.util.esr import generate_ref_number


class BusinessYear(JuntagricoBaseModel):
    """
    Business Year for Bills
    """
    start_date = models.DateField(_('start date'), unique=True)
    end_date = models.DateField(_('end date'))
    name = models.CharField(_('name'), max_length=20, null=True, blank=True, unique=True)

    def __str__(self):
        return self.name or str(self.start_date)

    class Meta:
        verbose_name = _('Business Year')
        verbose_name_plural = _('Business Years')

    def clean(self):
        # make sure end_date is before start_date
        if self.start_date and self.end_date:
            if self.end_date <= self.start_date:
                raise ValidationError({'end_date': _('Businessyear end_date must be after start_date.')})


class Bill(JuntagricoBaseModel):
    """
    Actuall Bill for billables
    """
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
    public_notes = models.TextField(_('Notes visible to {}').format(Config.vocabulary('member_pl')), null=True, blank=True)
    private_notes = models.TextField(_('Notes not visible to {}').format(Config.vocabulary('member_pl')), null=True, blank=True)

    # derived properties
    @property
    def member_name(self):
        if self.billable:
            return self.billable.primary_member_nullsave()
        return ""

    @property
    def paid(self):
        return self.amount <= self.amount_paid

    @property
    def amount_paid(self):
        return sum([p.amount for p in self.payments.all()])

    @property
    def state(self):
        amount_paid = self.amount_paid
        if amount_paid < self.amount:
            return _('unpaid')
        elif amount_paid == self.amount:
            return _('paid')
        else:
            return _('overpaid')

    @property
    def ref_number(self):
        if isinstance(self.billable, Subscription):
            billtype = 'subscription'
        if isinstance(self.billable, ExtraSubscription):
            billtype = 'extra'
        return generate_ref_number(billtype, self.pk, self.billable.pk)

    def __str__(self):
        return '{}'.format(self.id)

    class Meta:
        verbose_name = _('Bill')
        verbose_name_plural = _('Bills')


class Payment(JuntagricoBaseModel):
    """
    Payment for bill
    """
    bill = models.ForeignKey('Bill', related_name='payments',
                             null=False, blank=False,
                             on_delete=models.PROTECT, verbose_name=_('Bill'))
    paid_date = models.DateField(_('Payment date'), null=True, blank=True)
    amount = models.FloatField(_('Amount'), null=False, blank=False)
    private_notes = models.TextField(_('Notes not visible to {}').format(Config.vocabulary('member_pl')), null=True, blank=True)

    def __str__(self):
        return '{}'.format(self.bill.id)

    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payment')
