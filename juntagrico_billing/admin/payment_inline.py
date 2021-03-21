from django.contrib import admin
from juntagrico_billing.entity.payment import Payment


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1
    exclude = ['unique_id']
