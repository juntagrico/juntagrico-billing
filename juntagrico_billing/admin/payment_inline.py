from django.contrib import admin
from juntagrico_billing.entity.bill import Payment


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1
