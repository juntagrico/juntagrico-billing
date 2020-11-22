from juntagrico.admins import BaseAdmin


class PaymentAdmin(BaseAdmin):
    raw_id_fields = ['bill']
    list_display = ['bill', 'paid_date', 'amount', 'type']


class PaymentTypeAdmin(BaseAdmin):
    pass
