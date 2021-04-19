from django.contrib import admin
from django.urls import reverse
from django.utils.html import escape, mark_safe
from django.utils.translation import gettext as _
from juntagrico_billing.entity.bill import BillItem


class BillItemInline(admin.TabularInline):
    model = BillItem
    readonly_fields = ('item_kind_link',)
    fields = ('item_kind_link', 'custom_item_type', 'description', 'amount')
    extra = 1

    def item_kind_link(self, item):
        """
        generate a link to the subscription admin page
        """
        if item.subscription_part:
            subscription = item.subscription_part.subscription
            link = reverse("admin:juntagrico_subscription_change", args=[subscription.id])
            return mark_safe(f'<a href="{link}">{escape(item.item_kind)}</a>')

        return item.item_kind

    item_kind_link.short_description = _('item_kind')
