from datetime import date

import django.test
from juntagrico.entity.depot import Depot
from juntagrico.entity.member import Member
from juntagrico.entity.subs import Subscription, SubscriptionPart
from juntagrico.entity.subtypes import SubscriptionProduct, SubscriptionSize, SubscriptionType
from juntagrico.entity.billing import BillingPeriod

from juntagrico_billing.entity.account import MemberAccount, SubscriptionTypeAccount
from juntagrico_billing.entity.settings import Settings


class SubscriptionTestBase(django.test.TestCase):
    def setUp(self):
        subs_product = SubscriptionProduct.objects.create(
            name="Test-Product",
            description="Test-Product Description"
        )

        subs_size = SubscriptionSize.objects.create(
            name="Normal",
            long_name="Normale Grösse",
            units=1,
            product=subs_product
        )

        # subscription type and account
        self.subs_type = SubscriptionType.objects.create(
            name="Normal",
            size=subs_size,
            shares=1,
            required_assignments=5,
            price=1200,
        )

        SubscriptionTypeAccount.objects.create(
            subscriptiontype=self.subs_type,
            account="3001"
        )

        self.depot = Depot.objects.create(
            name="Das erste Depot",
            contact=self.create_member("Test", "Depot"),
            weekday=5,
        )

        self.subscription = self.create_subscription_and_member(self.subs_type,
                                                                date(2018, 1, 1),
                                                                date(2018, 1, 1),
                                                                None,
                                                                "Test",
                                                                "4321")

        # extra subscription product, size and account
        extra_product = SubscriptionProduct.objects.create(
            name="Extra1",
            description="Extra1 Product Description",
            is_extra=True
        )

        extra_size = SubscriptionSize.objects.create(
            name="Normal",
            long_name="Normal (extra)",
            units=1,
            product=extra_product,
        )

        self.extrasub_type = SubscriptionType.objects.create(
            name="Extra 1",
            size=extra_size,
            description="Extra1 Subscription",
            required_assignments=0,
            price=0.0
        )

        SubscriptionTypeAccount.objects.create(
            subscriptiontype=self.extrasub_type,
            account="3010"
        )

        self.extrasub_period1 = BillingPeriod.objects.create(
            type=self.extrasub_type,
            price=100,
            start_day=1,
            start_month=1,
            end_day=30,
            end_month=6,
            cancel_day=31,
            cancel_month=5
        )
        self.extrasub_period2 = BillingPeriod.objects.create(
            type=self.extrasub_type,
            price=200,
            start_day=1,
            start_month=7,
            end_day=31,
            end_month=12,
            cancel_day=30,
            cancel_month=11
        )

        Settings.objects.create(
            debtor_account="1100"
        )

    def create_member(self, first_name, last_name):
        member = Member.objects.create(
            first_name=first_name,
            last_name=last_name,
            email="%s@%s.ch" % (last_name, last_name),
            addr_street="Musterstrasse",
            addr_zipcode="8000",
            addr_location="Zürich",
            phone="01234567"
        )
        member.save()
        return member

    def create_subscription_and_member(self, type, start_date, activation_date, deactivation_date, name, account):
        member = self.create_member("Michael", name)    # need to set different names because e-mail must be unique
        subscription = Subscription.objects.create(
            depot=self.depot,
            start_date=start_date,
            end_date=deactivation_date,
            activation_date=activation_date,
            deactivation_date=deactivation_date
        )
        member.subscription = subscription
        member.save()
        subscription.primary_member = member
        member.join_subscription(subscription)
        # hack: need to set join_date, otherwise consistency checks fail
        sub_membership = member.subscriptionmembership_set.filter(subscription=subscription).first()
        sub_membership.join_date = activation_date
        sub_membership.save()
        subscription.save()

        part = SubscriptionPart.objects.create(
            subscription=subscription,
            type=type,
            activation_date=activation_date
        )
        part.save()

        # create account for member
        MemberAccount.objects.create(
            member=member,
            account=account
        )

        return subscription
