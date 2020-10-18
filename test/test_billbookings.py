from datetime import date
from test.test_base import SubscriptionTestBase

from juntagrico_billing.entity.bill import BusinessYear, Bill
from juntagrico_billing.util.billing import create_subscription_bill
from juntagrico_billing.util.bookings import get_bill_bookings

class BillBookingsTest(SubscriptionTestBase):
    
    def setUp(self):
        super().setUp()

        self.year = BusinessYear.objects.create(start_date=date(2018, 1, 1),
                                           end_date=date(2018, 12, 31),
                                           name="2018")

    def test_bill_bookings(self):
        bill = create_subscription_bill(self.subscription, self.year, self.year.start_date)    
        bookings = get_bill_bookings(date(2018, 1, 1), date(2018, 12, 31))  

        self.assertEquals(1, len(bookings)) 
        booking = bookings[0]

        self.assertEquals(self.year.start_date, booking.date)
        self.assertEquals(bill.id, booking.docnumber)
        self.assertEquals("Rechnung Abo Michael Test", booking.text)
        self.assertEquals("1100", booking.debit_account)
        # todo add account nr to test
        self.assertEquals("", booking.credit_account)
        self.assertEquals("", booking.member_account)
        self.assertEquals(1200.0, booking.price)


