from juntagrico.admins import BaseAdmin
from juntagrico_billing.admin.payment_inline import PaymentInline


class BillAdmin(BaseAdmin):
    raw_id_fields = ['billable', 'business_year']
    list_display = ['business_year', 'billable', 'bill_date', 'amount']
    inlines = [PaymentInline, ]
