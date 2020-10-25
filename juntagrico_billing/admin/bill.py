from juntagrico.admins import BaseAdmin
from juntagrico_billing.admin.payment_inline import PaymentInline
from juntagrico_billing.entity.bill import Bill


class BillAdmin(BaseAdmin):
    raw_id_fields = ['business_year']
    list_display = ['business_year', 'bill_date', 'amount']
    inlines = [PaymentInline, ]
