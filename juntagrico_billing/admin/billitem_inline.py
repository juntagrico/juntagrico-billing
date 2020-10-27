from django.contrib import admin
from juntagrico_billing.entity.bill import BillItem


class BillItemInline(admin.TabularInline):
    model = BillItem
    readonly_fields = ('item_kind',)
    fields = ('item_kind', 'description', 'amount')
    extra = 1
