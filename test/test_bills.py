from datetime import date
from decimal import Decimal
from django.conf import settings

from juntagrico.entity.subs import SubscriptionPart

from juntagrico_billing.util.billing import scale_subscription_price, scale_extrasubscription_price
from juntagrico_billing.util.billing import get_billable_items, create_bill, create_bills_for_items
from juntagrico_billing.entity.bill import Bill, BusinessYear
from test.test_base import SubscriptionTestBase


class ScaleSubscriptionPriceTest(SubscriptionTestBase):

    def test_price_by_date_fullyear(self):
        start_date = date(2018, 1, 1)
        end_date = date(2018, 12, 31)
        price_fullyear = scale_subscription_price(self.subscription,
                                                  start_date, end_date)
        self.assertEqual(1200.0, price_fullyear, "full year")

    def test_price_by_date_shifted_business_year(self):
        settings.BUSINESS_YEAR_START = {'day': 1, 'month': 7}
        try:
            start_date = date(2018, 7, 1)
            end_date = date(2019, 6, 30)
            price_fullyear = scale_subscription_price(self.subscription,
                                                      start_date, end_date)
            self.assertEqual(1200.0, price_fullyear, "full year")
        finally:
            del settings.BUSINESS_YEAR_START

    def test_price_by_date_partial_subscription(self):
        self.subscription.activation_date = date(2018, 7, 1)
        self.subscription.deactivation_date = date(2018, 9, 30)
        for part in self.subscription.parts.all():
            part.activation_date = date(2018, 7, 1)
            part.deactivation_date = date(2018, 9, 30)
            part.save()
        start_date = date(2018, 1, 1)
        end_date = date(2018, 12, 31)
        price = scale_subscription_price(self.subscription,
                                         start_date, end_date)
        price_expected = round(1200.0 * (31 + 31 + 30) / 365, 2)
        self.assertEqual(price_expected, price,
                         "quarter subscription over a year")


class ScaleExtraSubscriptionPriceTest(SubscriptionTestBase):
    expected_price = round(
        (100.0 * (31 + 30 + 31 + 30) / (31 + 28 + 31 + 30 + 31 + 30)) + (200.0 * (31 + 31 + 30 + 31) / (31 + 31 + 30 + 31 + 30 + 31)),
        2)

    def test_full_year(self):
        start_date = date(2018, 1, 1)
        end_date = date(2018, 12, 31)

        price = scale_extrasubscription_price(self.extrasubs, start_date, end_date)
        self.assertEqual(300.00, price, "full year")

    def test_first_half_year(self):
        # first half year is exactly 1. extrasub period
        start_date = date(2018, 1, 1)
        end_date = date(2018, 6, 30)

        price = scale_extrasubscription_price(self.extrasubs, start_date, end_date)
        self.assertEqual(100.00, price, "first half year")

    def test_second_half_year(self):
        # second half year is exactly 2. extrasub period
        start_date = date(2018, 7, 1)
        end_date = date(2018, 12, 31)

        price = scale_extrasubscription_price(self.extrasubs, start_date, end_date)
        self.assertEqual(200.00, price, "second half year")

    def test_partial_year(self):
        start_date = date(2018, 3, 1)
        end_date = date(2018, 10, 31)

        price = scale_extrasubscription_price(self.extrasubs, start_date, end_date)
        self.assertEquals(ScaleExtraSubscriptionPriceTest.expected_price, price, "partial year")

    def test_partial_active(self):
        # full year but partial active extrasubscription
        start_date = date(2018, 1, 1)
        end_date = date(2018, 12, 31)

        self.extrasubs.activation_date = date(2018, 3, 1)
        self.extrasubs.deactivation_date = date(2018, 10, 31)

        price = scale_extrasubscription_price(self.extrasubs, start_date, end_date)
        self.assertEquals(ScaleExtraSubscriptionPriceTest.expected_price, price, "partial active")


class BillSubscriptionsTests(SubscriptionTestBase):
    def setUp(self):
        super().setUp()

        # create some more subscriptions
        self.subs2 = self.create_subscription_and_member(self.subs_type,
                                                         date(2017, 1, 1), None, "Early", "Lastyear", "17321")
        self.subs3 = self.create_subscription_and_member(self.subs_type,
                                                         date(2018, 3, 1), None, "Later", "Thisyear", "17321")

        self.year = BusinessYear.objects.create(start_date=date(2018, 1, 1),
                                                end_date=date(2018, 12, 31),
                                                name="2018")


    def test_get_billable_subscriptions_without_bills(self):
        billable_items = get_billable_items(self.year)
        self.assertTrue(billable_items)
        billable_subscription_parts = [part for part in billable_items if isinstance(part, SubscriptionPart)]

        self.assertEqual(3, len(billable_subscription_parts))
        subscription = billable_subscription_parts[0].subscription
        self.assertEqual('Test', subscription.primary_member.last_name)


    def test_get_billable_subscriptions(self):
        # create bill for subs2
        bill = create_bill(self.subs2.parts.all(), self.year, self.year.start_date)

        billable_items = get_billable_items(self.year)
        self.assertTrue(billable_items)

        billable_subscription_parts = [part for part in billable_items if isinstance(part, SubscriptionPart)]

        # we expect only 2 billable subscriptions
        self.assertEqual(2, len(billable_subscription_parts))
        subscription = billable_subscription_parts[0].subscription
        self.assertEqual('Test', subscription.primary_member.last_name)

    def test_create_bill_multiple_members(self):
        # creating a bill for billable items from different members 
        # should result in an error
        billable_items = get_billable_items(self.year)
        with self.assertRaisesMessage(Exception, 'billable items belong to different members'):
            bill = create_bill(billable_items, self.year, self.year.start_date)

    def test_create_bill(self):
        billable_items = [self.subscription.parts.all()[0], self.extrasubs]
        bill = create_bill(billable_items, self.year, self.year.start_date)

        self.assertEquals(2, len(bill.items.all()))
        self.assertEquals('Abo, Zusatzabo', bill.item_kinds)


    def test_create_bill_for_all(self):
        
        billable_items = get_billable_items(self.year)
        bills = create_bills_for_items(billable_items, self.year, self.year.start_date)

        self.assertEqual(3, len(bills))

        # there should be no billable items left
        billable_items = get_billable_items(self.year)
        self.assertEqual(0, len(billable_items))

