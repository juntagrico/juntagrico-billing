from juntagrico.admins import BaseAdmin
from juntagrico_billing.admin.payment_inline import PaymentInline
from juntagrico_billing.admin.billitem_inline import BillItemInline
from juntagrico_billing.entity.bill import Bill


class BillAdmin(BaseAdmin):
    readonly_fields = ['business_year']
    list_display = ['id', 'business_year', 'member', 'bill_date', 'item_kinds', 'amount', 'paid']
    inlines = [BillItemInline, PaymentInline, ]
