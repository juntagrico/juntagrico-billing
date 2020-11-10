from datetime import date
from test.test_base import SubscriptionTestBase

from juntagrico_billing.entity.bill import BusinessYear, Payment, PaymentType
from juntagrico_billing.util.billing import create_bill
from juntagrico_billing.util.bookings import get_bill_bookings, get_payment_bookings

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
                                        
        self.subscription = self.create_subscription_and_member(self.subs_type, date(2018, 1, 1), date(2018, 1, 1), None,
                                                                "Michael", "Test", "4321")

        self.bill = create_bill(self.subscription.parts.all(), self.year, self.year.start_date) 
        self.payment1 = Payment.objects.create(
            bill = self.bill,
            paid_date = date(2018, 2, 1),
            amount = 500.0,
            type = self.paymenttype
        )  

        self.payment2 = Payment.objects.create(
            bill = self.bill,
            paid_date = date(2018, 7, 2),
            amount = 700.0,
            type = self.paymenttype
        )


    def test_bill_bookings(self):
        bookings = get_bill_bookings(self.year.start_date, self.year.end_date)  

        self.assertEquals(1, len(bookings)) 
        booking = bookings[0]

        self.assertEquals(self.year.start_date, booking.date)
        self.assertEquals("500011", booking.docnumber)
        self.assertEquals("Rechnung 1: Abo Michael Test", booking.text)
        self.assertEquals("1100", booking.debit_account)
        # todo add account nr to test
        self.assertEquals("3001", booking.credit_account)
        self.assertEquals("4321", booking.member_account)
        self.assertEquals(1200.0, booking.price)

    def test_payment_bookings(self):
        bookings = get_payment_bookings(self.year.start_date, self.year.end_date)

        self.assertEquals(2, len(bookings))
        booking = bookings[0]
        self.assertEquals(date(2018, 2, 1), booking.date)
        self.assertEquals('600001', booking.docnumber)
        self.assertEquals("Zahlung Rechnung 1: Abo Michael Test", booking.text)
        self.assertEquals(500.0, booking.price)
        self.assertEquals('1100', booking.credit_account)
        self.assertEquals('1010', booking.debit_account)
        self.assertEquals('4321', booking.member_account)




