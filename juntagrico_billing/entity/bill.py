from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext as _
from juntagrico.config import Config
from juntagrico.entity import JuntagricoBaseModel
from juntagrico.entity.extrasubs import ExtraSubscriptionType
from juntagrico.entity.subtypes import SubscriptionType
from juntagrico.entity.member import Member

from juntagrico_billing.util.esr import generate_ref_number


class BusinessYear(JuntagricoBaseModel):
    """
    Business Year for Billing.
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
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValidationError({'end_date': _('Businessyear end_date must be after start_date.')})


class Bill(JuntagricoBaseModel):
    """
    Bill (invoice) class.
    Consists of several BillItems currently for subscription parts and extrasubscriptions.
    """
    business_year = models.ForeignKey(BusinessYear, related_name='bills',
                                      null=False, blank=False,
                                      on_delete=models.PROTECT,
                                      verbose_name=_('Business Year'))

    member = models.ForeignKey(Member, related_name='bills',
                               null=False, blank=False,
                               on_delete=models.PROTECT,
                               verbose_name=_('Member'))

    bill_date = models.DateField(
        _('Billing date'))
    booking_date = models.DateField(
        _('Booking date'))

    amount = models.FloatField(_('Amount'), null=False, blank=False, default=0.0)
    paid = models.BooleanField(_('Paid'), null=False, blank=False, default=False)
    public_notes = models.TextField(_('Notes visible to {}').format(Config.vocabulary('member_pl')), null=True, blank=True)
    private_notes = models.TextField(_('Notes not visible to {}').format(Config.vocabulary('member_pl')), null=True, blank=True)

    # derived properties
    @property
    def amount_paid(self):
        return sum([p.amount for p in self.payments.all()])

    amount_paid.fget.short_description = _('Amount paid')

    @property
    def item_kinds(self):
        """
        List the kind of items on the bill.
        short description for displaying in lists.
        """
        return ', '.join([itm.item_kind for itm in self.items.all()])

    @property
    def description(self):
        """
        Concatenation of the BillItem descriptions, joined by line breaks.
        """
        return "\n".join([itm.description for itm in self.items.all()])

    def __str__(self):
        return '{}'.format(self.id)

    class Meta:
        verbose_name = _('Bill')
        verbose_name_plural = _('Bills')


class BillItem(JuntagricoBaseModel):
    """
    Item on a bill.
    Is created based on the state of billable items
    when the bill is created.
    Used for displaying details for the bill and
    for creating booking records.
    """
    bill = models.ForeignKey(Bill, related_name='items',
                             null=False, blank=False,
                             on_delete=models.CASCADE, verbose_name=_('Bill'))

    # a bill item has either a subscription type or a extrasubscription type assigned
    subscription_type = models.ForeignKey(SubscriptionType, related_name='bill_items',
                                          null=True, blank=True,
                                          on_delete=models.PROTECT, 
                                          verbose_name=_('Subscription'))
    extrasubscription_type = models.ForeignKey(ExtraSubscriptionType, related_name='bill_items',
                                               null=True, blank=True,
                                               on_delete=models.PROTECT, 
                                               verbose_name=_('Extrasubscription'))

    description = models.CharField(_('Description'), null=True, blank=True, max_length=100)

    amount = models.FloatField(_('Amount'), null=False, blank=False, default=0.0)

    # derived property
    @property
    def billable_reference(self):
        return self.subscription_type or self.extrasubscription_type

    @property
    def item_kind(self):
        """
        the type of the item.
        used as a short description the bill item.
        """
        if self.subscription_type:
            return _('Subscription')
        elif self.extrasubscription_type:
            return _('Extrasubscription')
        else:
            return ''

    item_kind.fget.short_description = _('Item kind')


class Payment(JuntagricoBaseModel):
    """
    Payment for bill
    """
    bill = models.ForeignKey('Bill', related_name='payments',
                             null=False, blank=False,
                             on_delete=models.PROTECT, verbose_name=_('Bill'))
    type = models.ForeignKey('PaymentType', related_name='payments',
                             null=False, blank=False,
                             on_delete=models.PROTECT, verbose_name=_('Payment type'))
    paid_date = models.DateField(_('Payment date'), null=True, blank=True)
    amount = models.FloatField(_('Amount'), null=False, blank=False, default=0.0)
    private_notes = models.TextField(_('Notes not visible to {}').format(Config.vocabulary('member_pl')), null=True, blank=True)

    def __str__(self):
        return '{}'.format(self.bill.id)

    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')


class PaymentType(JuntagricoBaseModel):
    """
    Payment type,
    defining bank and booking account
    """
    name = models.CharField(_('Name'), null=True, blank=True, max_length=50)
    iban = models.CharField('IBAN', null=True, blank=True, max_length=30)
    booking_account = models.CharField(_('Booking account'), max_length=10)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Payment type')
        verbose_name_plural = _('Payment types')
