from django.contrib import admin

from juntagrico_billing.admin.bill import BillAdmin
from juntagrico_billing.admin.businessyear import BusinessYearAdmin
from juntagrico_billing.admin.payment import PaymentAdmin, PaymentTypeAdmin
from juntagrico_billing.entity.account import MemberAccount, SubscriptionTypeAccount
from juntagrico_billing.entity.bill import Bill, BillItemType, BusinessYear
from juntagrico_billing.entity.payment import Payment, PaymentType
from juntagrico_billing.entity.settings import Settings


class MemberAccountInline(admin.TabularInline):
    model = MemberAccount
    verbose_name = 'Konto'
    verbose_name_plural = 'Konti'
    extra = 0


class SubscriptionTypeAccountInline(admin.TabularInline):
    model = SubscriptionTypeAccount
    verbose_name = 'Konto'
    verbose_name_plural = 'Konti'
    extra = 0


class SettingsAdmin(admin.ModelAdmin):
    model = Settings
    verbose_name = "Buchaltungs-Einstellungen"
    verbose_name_plural = verbose_name


class BillItemTypeAdmin(admin.ModelAdmin):
    pass


admin.site.register(Settings, SettingsAdmin)
admin.site.register(Bill, BillAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(PaymentType, PaymentTypeAdmin)
admin.site.register(BusinessYear, BusinessYearAdmin)
admin.site.register(BillItemType, BillItemTypeAdmin)
