from django.contrib import admin

from juntagrico_billing.admin.bill import BillAdmin
from juntagrico_billing.admin.businessyear import BusinessYearAdmin
from juntagrico_billing.admin.payment import PaymentAdmin
from juntagrico_billing.entity.account import MemberAccount, SubscriptionTypeAccount, ExtraSubscriptionCategoryAccount
from juntagrico_billing.entity.billing import Bill, Payment, BusinessYear
from juntagrico_billing.entity.settings import Settings

'''
Legacy stuff check what has to be converted
'''


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


class ExtraSubscriptionCategoryAccountInline(admin.TabularInline):
    model = ExtraSubscriptionCategoryAccount
    verbose_name = 'Konto'
    verbose_name_plural = 'Konti'
    extra = 0


class SettingsAdmin(admin.ModelAdmin):
    model = Settings
    verbose_name = "Buchaltungs-Einstellungen"
    verbose_name_plural = verbose_name


admin.site.register(Settings, SettingsAdmin)

'''
end of legacy
'''
admin.site.register(Bill, BillAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(BusinessYear, BusinessYearAdmin)