from django.db import models
from juntagrico.entity import JuntagricoBaseModel
from django.utils.translation import gettext as _
from juntagrico.config import Config


class Payment(JuntagricoBaseModel):
    """
    Payment for bill
    """
    bill = models.ForeignKey('Bill', related_name='payments',
                             null=False, blank=False,
                             on_delete=models.PROTECT, verbose_name=_('Bill'))
    type = models.ForeignKey('PaymentType', related_name='payments',
                             null=False, blank=False,
                             on_delete=models.PROTECT,
                             verbose_name=_('Payment type'))
    paid_date = models.DateField(_('Payment date'), null=True, blank=True)
    amount = models.FloatField(
        _('Amount'),
        null=False, blank=False, default=0.0)
    private_notes = models.TextField(
        _('Notes not visible to {}').format(Config.vocabulary('member_pl')),
        null=True, blank=True)
    unique_id = models.CharField(
        _('Unique Id'), max_length=50,
        null=True, blank=True, unique=True)

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
