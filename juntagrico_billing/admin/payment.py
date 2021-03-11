from juntagrico.admins import BaseAdmin


class PaymentAdmin(BaseAdmin):
    raw_id_fields = ['bill']
    list_display = ['bill', 'paid_date', 'amount', 'type']
    exclude = ['unique_id']


class PaymentTypeAdmin(BaseAdmin):
    pass
