from datetime import date

from juntagrico.entity.billing import BillingPeriod
from juntagrico.tests import JuntagricoTestCase

from juntagrico_billing.models.account import SubscriptionTypeAccount, MemberAccount
from juntagrico_billing.models.bill import BusinessYear
from juntagrico_billing.models.settings import Settings


class BillingTestCase(JuntagricoTestCase):
    @classmethod
    def setUpTestData(cls):
        # load from fixtures
        cls.load_members()
        # setup other objects
        cls.set_up_depots()
        cls.set_up_sub_types()
        cls.set_up_extra_sub_types()

        # adjust sub type
        cls.sub_type.price = 1200
        cls.sub_type.name = 'Normal'
        cls.sub_type.save()

        cls.extrasub_type.name = 'Extra 1'
        cls.extrasub_type.save()

        cls.year = cls.create_business_year()

        cls.subscription = cls.create_subscription_and_member(
            cls.sub_type, date(2018, 1, 1), None, "Test", "4321"
        )
        cls.part = cls.subscription.parts.first()

        SubscriptionTypeAccount.objects.create(
            subscriptiontype=cls.sub_type,
            account="3001"
        )

        SubscriptionTypeAccount.objects.create(
            subscriptiontype=cls.extrasub_type,
            account="3010"
        )

        cls.extrasub_period1 = BillingPeriod.objects.create(
            type=cls.extrasub_type,
            price=100,
            start_day=1,
            start_month=1,
            end_day=30,
            end_month=6,
            cancel_day=31,
            cancel_month=5
        )
        cls.extrasub_period2 = BillingPeriod.objects.create(
            type=cls.extrasub_type,
            price=200,
            start_day=1,
            start_month=7,
            end_day=31,
            end_month=12,
            cancel_day=30,
            cancel_month=11
        )

        cls.settings = Settings.objects.create(
            debtor_account="1100"
        )

    @staticmethod
    def create_billing_member(first_name, last_name):
        return JuntagricoTestCase.create_member(
            "%s@%s.ch" % (last_name, last_name),
            first_name=first_name,
            last_name=last_name,
            addr_street="Musterstrasse",
            addr_zipcode="8000",
            addr_location="Zürich",
            phone="01234567"
        )

    @classmethod
    def create_subscription_and_member(cls, type, activation_date, deactivation_date, last_name, account):
        member = cls.create_billing_member("Michael", last_name)  # need to set different names because e-mail must be unique
        subscription = cls.create_sub(
            depot=cls.depot,
            activation_date=activation_date,
            deactivation_date=deactivation_date,
            parts=[type]
        )
        member.join_subscription(subscription, True)

        # create account for member
        MemberAccount.objects.create(
            member=member,
            account=account
        )

        return subscription

    @staticmethod
    def create_business_year(year=2018):
        return BusinessYear.objects.create(
            start_date=date(year, 1, 1),
            end_date=date(year, 12, 31),
            name=str(year)
        )
