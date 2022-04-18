from django.utils.translation import gettext as _
from django.urls import reverse
from django.utils.html import mark_safe
from django.contrib.admin import display
from juntagrico.admins import BaseAdmin

from juntagrico_billing.admin.billitem_inline import BillItemInline
from juntagrico_billing.admin.payment_inline import PaymentInline
from juntagrico_billing.util.billing import recalc_bill, publish_bills


def set_notification_sent(modeladmin, request, queryset):
    queryset.update(notification_sent=True)


set_notification_sent.short_description = _("Set flag for 'notification sent'")


def reset_notification_sent(modeladmin, request, queryset):
    queryset.update(notification_sent=False)


reset_notification_sent.short_description = _("Reset flag for 'notification sent'")


def do_recalc_bill(modeladmin, request, queryset):
    for bill in queryset.all():
        recalc_bill(bill)


do_recalc_bill.short_description = _("Recalculate bills")


def do_publish_bills(modeladmin, request, queryset):
    bill_ids = [bill.id for bill in queryset.all()]
    publish_bills(bill_ids)


do_publish_bills.short_description = _("Publish bills")


class BillAdmin(BaseAdmin):
    readonly_fields = ['business_year']
    search_fields = ['id', 'member__first_name', 'member__last_name']
    list_display = [
        'id', 'business_year', 'member', 'bill_date', 'item_kinds',
        'amount_f', 'amount_open_f', 'paid', 'published', 'user_bill_link']
    inlines = [BillItemInline, PaymentInline, ]
    actions = [
        do_recalc_bill, do_publish_bills, set_notification_sent,
        reset_notification_sent]

    @display(description=_('Amount'))
    def amount_f(self, bill):
        return f'{bill.amount:8.2f}'

    @display(description=_('Amount open'))
    def amount_open_f(self, bill):
        return f'{bill.amount_open:8.2f}'

    def user_bill_link(self, bill):
        """
        generate a link to the user bill
        """
        link = reverse("jb:user-bill", args=[bill.id])
        return mark_safe(f'<a href="{link}">{bill.id}</a>')

    user_bill_link.short_description = _('User view')
