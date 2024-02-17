from django.contrib import admin
from juntagrico_billing.models.payment import Payment


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1
    exclude = ['unique_id']
