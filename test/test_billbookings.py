from datetime import date

from juntagrico.entity.extrasubs import ExtraSubscription

from juntagrico_billing.entity.bill import BusinessYear, Payment, PaymentType
from juntagrico_billing.util.billing import create_bill
from juntagrico_billing.util.bookings import get_bill_bookings, get_payment_bookings
from test.test_base import SubscriptionTestBase


class BillBookingsTest(SubscriptionTestBase):

    def setUp(self):
        super().setUp()

        self.year = BusinessYear.objects.create(start_date=date(2018, 1, 1),
                                                end_date=date(2018, 12, 31),
                                                name="2018")

        self.paymenttype = PaymentType.objects.create(
            name="ABS",
            iban="CH4108390031346010006",
            booking_account="1010")

        self.subscription = self.create_subscription_and_member(self.subs_type, date(2018, 1, 1), date(2018, 1, 1), None, "Test", "4321")

        self.extrasubs = ExtraSubscription.objects.create(
            main_subscription=self.subscription,
            activation_date=date(2018, 1, 1),
            type=self.extrasub_type)

        items = list(self.subscription.parts.all()) + [self.extrasubs]

        self.bill = create_bill(items, self.year, self.year.start_date)

        self.payment1 = Payment.objects.create(
            bill=self.bill,
            paid_date=date(2018, 2, 1),
            amount=500.0,
            type=self.paymenttype
        )

        self.payment2 = Payment.objects.create(
            bill=self.bill,
            paid_date=date(2018, 7, 2),
            amount=700.0,
            type=self.paymenttype
        )

    def test_bill_bookings(self):
        bookings = get_bill_bookings(self.year.start_date, self.year.end_date)

        self.assertEquals(2, len(bookings))
        booking = bookings[0]

        self.assertEquals(self.year.start_date, booking.date)
        self.assertEquals("500011", booking.docnumber)
        self.assertEquals("Rg 1: Abo Michael Test", booking.text)
        self.assertEquals("1100", booking.debit_account)
        self.assertEquals("3001", booking.credit_account)
        self.assertEquals("4321", booking.member_account)
        self.assertEquals(1200.0, booking.price)

        booking = bookings[1]

        self.assertEquals(self.year.start_date, booking.date)
        self.assertEquals("500012", booking.docnumber)
        self.assertEquals("Rg 1: Zusatzabo Michael Test", booking.text)
        self.assertEquals("1100", booking.debit_account)
        self.assertEquals("3010", booking.credit_account)
        self.assertEquals("4321", booking.member_account)
        self.assertEquals(300.0, booking.price)

    def test_payment_bookings(self):
        bookings = get_payment_bookings(self.year.start_date, self.year.end_date)

        self.assertEquals(2, len(bookings))
        booking = bookings[0]
        self.assertEquals(date(2018, 2, 1), booking.date)
        self.assertEquals('600001', booking.docnumber)
        self.assertEquals("Zlg Rg 1: Abo, Zusatzabo Michael Test", booking.text)
        self.assertEquals(500.0, booking.price)
        self.assertEquals('1100', booking.credit_account)
        self.assertEquals('1010', booking.debit_account)
        self.assertEquals('4321', booking.member_account)
