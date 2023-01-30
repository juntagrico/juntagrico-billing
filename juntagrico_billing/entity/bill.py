from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext as _
from juntagrico.config import Config
from juntagrico.entity import JuntagricoBaseModel
from juntagrico.entity.member import Member
from juntagrico.entity.subs import SubscriptionPart


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
    published = models.BooleanField(_('Published'), default=False)
    notification_sent = models.BooleanField(_('Notification sent'), null=False, blank=False, default=False)
    vat_rate = models.FloatField(_('VAT Rate'), null=False, blank=False, default=0.0)

    # derived properties
    @property
    def amount_paid(self):
        return sum([p.amount for p in self.payments.all()])

    amount_paid.fget.short_description = _('Amount paid')

    @property
    def amount_open(self):
        return self.amount - self.amount_paid

    amount_open.fget.short_description = _('Amount open')

    @property
    def vat_amount(self):
        return sum([itm.vat_amount for itm in self.items.all()])

    vat_amount.fget.short_description = _('VAT Amount')

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
        return "\n".join([str(itm) for itm in self.items.all()])

    @property
    def ordered_items(self):
        """
        Bill items ordered for display.
        1. Subscription ordered by id
        2. Extrasubscriptions ordered by id
        3. Custom Items ordered by type and id
        """
        def order_key(itm):
            if itm.subscription_part:
                if itm.subscription_part.type.size.product.is_extra:
                    return (1, itm.id)
                else:
                    return (0, itm.id)
            elif itm.custom_item_type:
                return (2, itm.custom_item_type.id, itm.id)
            else:
                # itm without reference (unexpected)
                return (3, None)

        return sorted(self.items.all(), key=order_key)

    def __str__(self):
        return '{}'.format(self.id)

    class Meta:
        verbose_name = _('Bill')
        verbose_name_plural = _('Bills')


class BillItemType(JuntagricoBaseModel):
    """
    type definition for custom bill items (other than
    subscriptions or extra-subscriptions).
    """
    name = models.CharField(_('Name'), max_length=50)
    booking_account = models.CharField(_('Booking account'), max_length=10)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Custom Bill-Item Type')
        verbose_name_plural = _('Custom Bill-Item Types')


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

    # a bill item has either a subscription part
    # or a custom item_type assigned
    subscription_part = models.ForeignKey(
        SubscriptionPart, related_name='bill_items',
        null=True, blank=True, on_delete=models.PROTECT,
        verbose_name=_('{} Part').format(
            Config.vocabulary('subscription')))

    custom_item_type = models.ForeignKey(
        BillItemType, related_name='bill_items',
        null=True, blank=True, on_delete=models.PROTECT,
        verbose_name=_('Custom item type'))

    description = models.CharField(_('Description'), null=False, blank=True, max_length=100)

    amount = models.FloatField(_('Amount'), null=False, blank=False, default=0.0)

    vat_amount = models.FloatField(_('VAT Amount'), null=False, blank=False, default=0.0)

    def __str__(self):
        if self.subscription_part:
            return self.subscription_part.type.long_name or\
                self.subscription_part.type.size.name
        elif self.custom_item_type:
            return ('%s %s' % (self.custom_item_type.name, self.description)).strip()
        else:
            return self.description

    @property
    def item_kind(self):
        """
        the type of the item.
        used as a short description the bill item.
        """
        if self.subscription_part:
            if self.subscription_part.type.size.product.is_extra:
                return _('Extrasubscription')
            else:
                return _('Subscription')
        elif self.custom_item_type:
            return self.custom_item_type.name
        else:
            return ''

    item_kind.fget.short_description = _('Item kind')

    class Meta:
        verbose_name = _('Bill item')
        verbose_name_plural = _('Bill items')

    def save(self, *args, **kwargs):
        """
        save override to automatically recalculate the vat amount
        """
        # calc vat only for subscription_part items
        if self.bill and self.subscription_part:
            vat_rate = self.bill.vat_rate
            self.vat_amount = round(self.amount / (1 + vat_rate) * vat_rate, 2)
        else:
            self.vat_amount = 0.0

        super().save(*args, **kwargs)
