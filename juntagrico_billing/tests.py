import django.test
from juntagrico.models import *

from juntagrico_billing.entity.account import MemberAccount
from juntagrico_billing.entity.settings import Settings
from juntagrico_billing.util.bookings import subscription_bookings_by_date, gen_document_number, \
    extrasub_bookings_by_date


class SubscriptionTestBase(django.test.TestCase):
    def setUp(self):
        member = Member.objects.create(
            first_name="Michael",
            last_name="Test",
            email="test@test.ch",
            addr_street="Musterstrasse",
            addr_zipcode="8000",
            addr_location="Zürich",
            phone="01234567"
        )

        subs_size = SubscriptionSize.objects.create(
            name="Normal",
            long_name="Normale Grösse",
            units=1
        )

        subs_type = SubscriptionType.objects.create(
            name="Normal",
            size=subs_size,
            shares=1,
            required_assignments=5,
            price=1200,
        )

        depot = Depot.objects.create(
            code="Depot 1",
            name="Das erste Depot",
            contact=member,
            weekday=5,
        )

        self.subs = Subscription.objects.create(
            depot=depot,
            primary_member=member,
            active=True,
            activation_date=date(2018, 1, 1)
        )
        TSST.objects.create(
            subscription=self.subs,
            type=subs_type
        )

        extrasub_category = ExtraSubscriptionCategory.objects.create(
            name="ExtraCat1"
        )

        extrasub_type = ExtraSubscriptionType.objects.create(
            name="Extra 1",
            size="Extragross",
            description="Extra Subscription",
            category=extrasub_category
        )

        extrasub_period1 = ExtraSubBillingPeriod.objects.create(
            type=extrasub_type,
            price=100,
            start_day=1,
            start_month=1,
            end_day=30,
            end_month=6,
            cancel_day=31,
            cancel_month=5
        )
        extrasub_period2 = ExtraSubBillingPeriod.objects.create(
            type=extrasub_type,
            price=200,
            start_day=1,
            start_month=7,
            end_day=31,
            end_month=12,
            cancel_day=30,
            cancel_month=11
        )

        self.extrasubs = ExtraSubscription.objects.create(
            main_subscription=self.subs,
            active=True,
            activation_date=date(2018, 1, 1),
            type=extrasub_type
        )

        # create account for member
        MemberAccount.objects.create(
            member=member,
            account="4321"
        )

        Settings.objects.create(
            debtor_account="1100"
        )


class SubscriptionBookingsTest(SubscriptionTestBase):
    def test_subscription_booking_full_year(self):
        start_date = date(2018, 1, 1)
        end_date = date(2018, 12, 31)
        bookings_list = subscription_bookings_by_date(start_date, end_date)
        self.assertEqual(1, len(bookings_list))
        self.assertEqual(1200.0, bookings_list[0].price)
        self.assertEqual(start_date, bookings_list[0].date)
        self.assertEqual("180101000000001000000001", bookings_list[0].docnumber)

    def test_subscription_booking_part_year(self):
        start_date = date(2018, 1, 1)
        end_date = date(2018, 12, 31)
        # modify subscription to last from 1.7. - 30.09.
        self.subs.activation_date = date(2018, 7, 1)
        self.subs.deactivation_date = date(2018, 9, 30)
        self.subs.save()
        bookings_list = subscription_bookings_by_date(start_date, end_date)
        self.assertEqual(1, len(bookings_list))
        booking = bookings_list[0]
        price_expected = 0.99  # special marker price for partial interval subscription
        self.assertEqual(price_expected, booking.price)
        self.assertEqual(date(2018, 7, 1), booking.date)
        self.assertEqual("180101000000001000000001", booking.docnumber)
        self.assertEqual("1100", booking.debit_account)
        self.assertEqual("", booking.credit_account)  # subscriptiontype account is not assigned
        self.assertEqual("4321", booking.member_account)
        self.assertEqual("Abo: Normal - Grösse: Normal, Michael Test, Teilperiode 01.07.18 - 30.09.18", booking.text)

    def test_generate_document_number_for_subscription(self):
        docnumber = gen_document_number(self.subs, date(2018, 1, 1))
        docnumber_expected = "180101000000001000000001"
        self.assertEqual(docnumber_expected, docnumber, "document_number for subscription")


class ExtraSubscriptionBookingsTest(SubscriptionTestBase):

    def test_generate_document_number_for_extra_subscription(self):
        docnumber = gen_document_number(self.extrasubs, date(2018, 1, 1))
        docnumber_expected = "180101000000001000000002"
        self.assertEqual(docnumber_expected, docnumber, "document_number for extra subscription")

    def test_generate_document_number_with_empty_member(self):
        self.subs.primary_member = None
        docnumber = gen_document_number(self.subs, date(2018, 1, 1))
        docnumber_expected = "180101000000000000000001"
        self.assertEqual(docnumber_expected, docnumber, "document_number with empty member")

    def test_bookings_full_year(self):
        start_date = date(2018, 1, 1)
        end_date = date(2018, 12, 31)
        bookings_list = extrasub_bookings_by_date(start_date, end_date)
        self.assertEqual(2, len(bookings_list))

        booking = bookings_list[0]
        self.assertEqual(100, booking.price)
        self.assertEqual(date(2018, 1, 1), booking.date)
        self.assertEqual("180101000000001000000002", booking.docnumber)
        self.assertEqual("1100", booking.debit_account)
        self.assertEqual("", booking.credit_account)  # subscriptiontype account is not assigned
        self.assertEqual("4321", booking.member_account)
        self.assertEqual("Zusatz: Extra 1, 01.01.18-30.06.18, Michael Test", booking.text)

        booking = bookings_list[1]
        self.assertEqual(200, booking.price)
        self.assertEqual(date(2018, 7, 1), booking.date)
        self.assertEqual("180701000000001000000002", booking.docnumber)
        self.assertEqual("1100", booking.debit_account)
        self.assertEqual("", booking.credit_account)  # subscriptiontype account is not assigned
        self.assertEqual("4321", booking.member_account)
        self.assertEqual("Zusatz: Extra 1, 01.07.18-31.12.18, Michael Test", booking.text)

    def test_bookings_partial_period(self):
        """
        bookings for full year interval.
        extra-subscription is activated after the start of the interval.
        the first period should be marked with price of 0.99.
        """
        self.extrasubs.activation_date = date(2018, 3, 1)
        self.extrasubs.save()

        start_date = date(2018, 1, 1)
        end_date = date(2018, 12, 31)
        bookings_list = extrasub_bookings_by_date(start_date, end_date)
        self.assertEqual(2, len(bookings_list))

        booking = bookings_list[0]
        self.assertEqual(0.99, booking.price)
        self.assertEqual(date(2018, 1, 1), booking.date)
        self.assertEqual("180101000000001000000002", booking.docnumber)
        self.assertEqual("1100", booking.debit_account)
        self.assertEqual("", booking.credit_account)  # subscriptiontype account is not assigned
        self.assertEqual("4321", booking.member_account)
        self.assertEqual("Zusatz: Extra 1, 01.03.18-30.06.18, Michael Test", booking.text)

        booking = bookings_list[1]
        self.assertEqual(200, booking.price)
        self.assertEqual(date(2018, 7, 1), booking.date)
        self.assertEqual("180701000000001000000002", booking.docnumber)
        self.assertEqual("1100", booking.debit_account)
        self.assertEqual("", booking.credit_account)  # subscriptiontype account is not assigned
        self.assertEqual("4321", booking.member_account)
        self.assertEqual("Zusatz: Extra 1, 01.07.18-31.12.18, Michael Test", booking.text)

    def test_bookings_half_year(self):
        """
        bookings for half year interval.
        only 1 period is considered.
        """
        start_date = date(2018, 1, 1)
        end_date = date(2018, 6, 30)
        bookings_list = extrasub_bookings_by_date(start_date, end_date)
        self.assertEqual(1, len(bookings_list))

        booking = bookings_list[0]
        self.assertEqual(100, booking.price)
        self.assertEqual(date(2018, 1, 1), booking.date)
        self.assertEqual("180101000000001000000002", booking.docnumber)
        self.assertEqual("1100", booking.debit_account)
        self.assertEqual("", booking.credit_account)
        self.assertEqual("4321", booking.member_account)
        self.assertEqual("Zusatz: Extra 1, 01.01.18-30.06.18, Michael Test", booking.text)

    def test_bookings_overlapping(self):
        """
        bookings for an interval overlapping the extra-subscription periods.
        we get 2 bookings marked with "partial" price of 0.99.
        """
        start_date = date(2018, 2, 1)
        end_date = date(2018, 11, 30)
        bookings_list = extrasub_bookings_by_date(start_date, end_date)
        self.assertEqual(2, len(bookings_list))

        booking = bookings_list[0]
        self.assertEqual(0.99, booking.price)
        self.assertEqual(date(2018, 1, 1), booking.date)
        self.assertEqual("180101000000001000000002", booking.docnumber)
        self.assertEqual("1100", booking.debit_account)
        self.assertEqual("", booking.credit_account)
        self.assertEqual("4321", booking.member_account)
        self.assertEqual("Zusatz: Extra 1, 01.02.18-30.06.18, Michael Test", booking.text)

        booking = bookings_list[1]
        self.assertEqual(0.99, booking.price)
        self.assertEqual(date(2018, 7, 1), booking.date)
        self.assertEqual("180701000000001000000002", booking.docnumber)
        self.assertEqual("1100", booking.debit_account)
        self.assertEqual("", booking.credit_account)
        self.assertEqual("4321", booking.member_account)
        self.assertEqual("Zusatz: Extra 1, 01.07.18-30.11.18, Michael Test", booking.text)
