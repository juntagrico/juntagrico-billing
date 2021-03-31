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
        for subscriptions and extrasubscriptions.
        """
        member = item.bill.member
        subscription = None
        if item.subscription_type:
            subs_parts = item.subscription_type.subscription_parts \
                .filter(subscription__primary_member=member)
            if subs_parts:
                subscription = subs_parts[0].subscription
        elif item.extrasubscription_type:
            extrasubs = item.extrasubscription_type.extra_subscriptions \
                .filter(main_subscription__primary_member=member)
            if extrasubs:
                subscription = extrasubs[0].main_subscription
        if subscription:
            link = reverse("admin:juntagrico_subscription_change", args=[subscription.id])
            return mark_safe(f'<a href="{link}">{escape(item.item_kind)}</a>')

        return item.item_kind

    item_kind_link.short_description = _('item_kind')
