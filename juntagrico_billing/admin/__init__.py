from django.contrib import admin

from juntagrico.entity.member import Member
from juntagrico.entity.subtypes import SubscriptionType
from juntagrico.util import addons

from juntagrico_billing.admin.bill import BillAdmin
from juntagrico_billing.admin.businessyear import BusinessYearAdmin
from juntagrico_billing.admin.payment import PaymentAdmin, PaymentTypeAdmin
from juntagrico_billing.models.account import MemberAccount, SubscriptionTypeAccount
from juntagrico_billing.models.bill import Bill, BillItemType, BusinessYear
from juntagrico_billing.models.payment import Payment, PaymentType
from juntagrico_billing.models.settings import Settings


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


# add inlines on juntagrico models
addons.config.register_model_inline(Member, MemberAccountInline)
addons.config.register_model_inline(SubscriptionType, SubscriptionTypeAccountInline)


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
