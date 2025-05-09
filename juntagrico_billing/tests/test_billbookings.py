from datetime import date

from juntagrico.entity.subs import SubscriptionPart
from juntagrico_billing.models.bill import BillItem, BillItemType
from juntagrico_billing.models.payment import Payment, PaymentType
from juntagrico_billing.util.billing import create_bill
from juntagrico_billing.util.bookings import get_bill_bookings, get_payment_bookings
from . import BillingTestCase


class BillBookingsTest(BillingTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.paymenttype = PaymentType.objects.create(
            name="ABS",
            iban="CH4108390031346010006",
            booking_account="1010"
        )

        cls.extrasubs = SubscriptionPart.objects.create(
            subscription=cls.subscription,
            activation_date=date(2018, 1, 1),
            type=cls.extrasub_type
        )

        items = list(cls.subscription.parts.all())
        cls.bill = create_bill(items, cls.year, cls.year.start_date, 0.0)

        cls.payment1 = Payment.objects.create(
            bill=cls.bill,
            paid_date=date(2018, 2, 1),
            amount=500.0,
            type=cls.paymenttype
        )

        cls.payment2 = Payment.objects.create(
            bill=cls.bill,
            paid_date=date(2018, 7, 2),
            amount=700.0,
            type=cls.paymenttype
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

    def test_negative_payment_bookings(self):
        """
        test negative payment bookings

        booking amount should always be positive
        and credit and debit account should be exchanged
        """
        self.payment1.amount = -500.0
        self.payment1.save()

        bookings = get_payment_bookings(self.year.start_date, self.year.end_date)

        self.assertEquals(2, len(bookings))
        booking = bookings[0]
        self.assertEquals(date(2018, 2, 1), booking.date)
        self.assertEquals('600001', booking.docnumber)
        self.assertEquals("Zlg Rg 1: Abo, Zusatzabo Michael Test", booking.text)
        self.assertEquals(500.0, booking.price)
        self.assertEquals('1100', booking.debit_account)
        self.assertEquals('1010', booking.credit_account)
        self.assertEquals('4321', booking.member_account)


class BillWithCustomItemBookingsTest(BillingTestCase):
    def test_get_bill_bookings(self):
        item_type1 = BillItemType(name='Custom Item 1', booking_account='2211')
        item_type1.save()
        item_type2 = BillItemType(name='Custom Item 2', booking_account='2212')
        item_type2.save()

        bill = create_bill(self.subscription.parts.all(), self.year, self.year.start_date, 0.0)
        item = BillItem(bill=bill, custom_item_type=item_type1, amount=100.0)
        item.save()
        item = BillItem(bill=bill, custom_item_type=item_type2, amount=200.0)
        item.save()
        bill.save()

        # get bookigs
        bookings = get_bill_bookings(self.year.start_date, self.year.end_date)

        self.assertEquals(3, len(bookings))

        booking = bookings[1]
        self.assertEquals(self.year.start_date, booking.date)
        self.assertEquals("500012", booking.docnumber)
        self.assertEquals("Rg 1: Custom Item 1 Michael Test", booking.text)
        self.assertEquals("1100", booking.debit_account)
        self.assertEquals("2211", booking.credit_account)
        self.assertEquals("4321", booking.member_account)
        self.assertEquals(100.0, booking.price)

        booking = bookings[2]
        self.assertEquals(self.year.start_date, booking.date)
        self.assertEquals("500013", booking.docnumber)
        self.assertEquals("Rg 1: Custom Item 2 Michael Test", booking.text)
        self.assertEquals("1100", booking.debit_account)
        self.assertEquals("2212", booking.credit_account)
        self.assertEquals("4321", booking.member_account)
        self.assertEquals(200.0, booking.price)

    def test_get_bill_bookings_negative(self):
        """
        custom bill items with negative amount
        should result in bookings with credit and debit
        exchanged and positive amount.
        """
        item_type1 = BillItemType(name='Custom Item 1', booking_account='2211')
        item_type1.save()

        bill = create_bill(self.subscription.parts.all(), self.year, self.year.start_date, 0.0)
        item = BillItem(bill=bill, custom_item_type=item_type1, amount=-100.0)
        item.save()

        # get bookigs
        bookings = get_bill_bookings(self.year.start_date, self.year.end_date)

        self.assertEquals(2, len(bookings))

        booking = bookings[1]
        self.assertEquals(self.year.start_date, booking.date)
        self.assertEquals("500012", booking.docnumber)
        self.assertEquals("Rg 1: Custom Item 1 Michael Test", booking.text)

        # credit and debit account are exchanged
        # and amount is positive
        self.assertEquals("2211", booking.debit_account)
        self.assertEquals("1100", booking.credit_account)
        self.assertEquals("4321", booking.member_account)
        self.assertEquals(100.0, booking.price)
