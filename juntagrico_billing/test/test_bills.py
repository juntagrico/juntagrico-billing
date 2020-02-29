from datetime import date
from django.conf import settings

from juntagrico_billing.test.test_base import SubscriptionTestBase
from juntagrico_billing.util.bills import scale_subscription_price
from juntagrico_billing.util.bills import get_billable_subscriptions
from juntagrico_billing.entity.billing import Bill, BusinessYear


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

    def test_price_by_date_quarter(self):
        start_date = date(2018, 4, 1)
        end_date = date(2018, 6, 30)
        price_quarter = scale_subscription_price(self.subscription,
                                                 start_date, end_date)
        price_quarter_expected = 1200.0 * (30 + 31 + 30) / 365
        self.assertEqual(price_quarter_expected, price_quarter,
                         "second quarter")

    def test_price_by_date_partial_subscription(self):
        self.subscription.activation_date = date(2018, 7, 1)
        self.subscription.deactivation_date = date(2018, 9, 30)
        start_date = date(2018, 1, 1)
        end_date = date(2018, 12, 31)
        price = scale_subscription_price(self.subscription,
                                         start_date, end_date)
        price_expected = 1200.0 * (31 + 31 + 30) / 365
        self.assertEqual(price_expected, price,
                         "quarter subscription over a year")

class BillSubscriptionsTests(SubscriptionTestBase):
    def setUp(self):
        super().setUp()

        # create some more subscriptions
        self.subs2 = self.create_subscription_and_member(self.subs_type, 
                    date(2017, 1, 1), None, "Early", "Lastyear", "17321")
        self.subs3 = self.create_subscription_and_member(self.subs_type, 
                    date(2018, 3, 1), None, "Later", "Thisyear", "17321")


    def test_businessyear_end_date(self):
        year = BusinessYear.objects.create(start_date=date(2018,1,1),
                                            name="2018")

        self.assertEqual(date(2018, 12, 31), year.end_date)


    def test_get_billable_subscriptions_without_bills(self):
        year = BusinessYear.objects.create(start_date=date(2018,1,1),
                                            name="2018")
        to_bill_list = get_billable_subscriptions(year)

        self.assertEqual(3, len(to_bill_list))
        subscription = to_bill_list[0].subscription
        self.assertEqual('Test', subscription.primary_member.last_name)


    def test_get_billable_subscriptions(self):
        year = BusinessYear.objects.create(start_date=date(2018,1,1),
                                            name="2018")

        # create bill for subs2
        bill = Bill.objects.create(billable=self.subs2, business_year=year, 
                    bill_date=date(2018, 1, 1), amount=1200)
        bill.save()

        to_bill_list = get_billable_subscriptions(year)

        # we expect only 2 billable subscriptions
        self.assertEqual(2, len(to_bill_list))
        subscription = to_bill_list[0]
        self.assertEqual('Test', subscription.primary_member.last_name)
