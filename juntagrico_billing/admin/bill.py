from django.utils.translation import gettext as _
from juntagrico.admins import BaseAdmin

from juntagrico_billing.admin.billitem_inline import BillItemInline
from juntagrico_billing.admin.payment_inline import PaymentInline
from juntagrico_billing.util.billing import recalc_bill


def set_notification_sent(modeladmin, request, queryset):
    queryset.update(notification_sent=True)


set_notification_sent.short_description = _("Set flag for 'notification sent'")


def reset_notification_sent(modeladmin, request, queryset):
    queryset.update(notification_sent=False)


reset_notification_sent.short_description = _("Reset flag for 'notification sent'")


def do_recalc_bill(modeladmin, request, queryset):
    for bill in queryset.all():
        recalc_bill(bill)


do_recalc_bill.short_description = _("Recalculate bill")


class BillAdmin(BaseAdmin):
    readonly_fields = ['business_year']
    search_fields = ['id', 'member__first_name', 'member__last_name']
    list_display = ['id', 'business_year', 'member', 'bill_date', 'item_kinds', 'amount', 'paid']
    inlines = [BillItemInline, PaymentInline, ]
    actions = [do_recalc_bill, set_notification_sent, reset_notification_sent]
