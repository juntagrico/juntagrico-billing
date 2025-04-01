from datetime import date
from . import BillingTestCase
from juntagrico_billing.models.bill import Bill, BillItem, BillItemType
from juntagrico_billing.models.payment import Payment, PaymentType
from juntagrico_billing.util.billing import get_memberbalances


class MemberBalanceTest(BillingTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        def create_bill(member, date, amount):
            bill = Bill.objects.create(
                business_year=cls.year, member=member, published=True,
                bill_date=date, booking_date=date)
            BillItem.objects.create(
                bill=bill, custom_item_type=cls.item_type1,
                amount=amount
            )
            bill.save()
            return bill

        def create_payment(bill, amount, date):
            payment = Payment.objects.create(
                bill=bill, amount=amount, paid_date=date, type=cls.payment_type
            )
            payment.save()
            return payment

        # create a payment type
        cls.payment_type = PaymentType.objects.create(name='Test Payment Type')

        cls.member1 = cls.create_billing_member("Alpha", "Member1")
        cls.member2 = cls.create_billing_member("Beta", "Member2")

        cls.item_type1 = BillItemType.objects.create(name='Test Item Type', booking_account='2211')

        # create some bills
        cls.bill1 = create_bill(cls.member1, date(2024, 10, 1), 1200)
        cls.bill2 = create_bill(cls.member1, date(2024, 11, 1), 1300)
        cls.bill3 = create_bill(cls.member1, date(2025, 2, 1), 1400)
        cls.bill4 = create_bill(cls.member2, date(2024, 10, 1), 1500)
        cls.bill5 = create_bill(cls.member2, date(2024, 11, 1), 1600)

        # create some payments
        create_payment(cls.bill1, 400, date(2024, 10, 15))
        create_payment(cls.bill1, 800, date(2024, 11, 15))
        create_payment(cls.bill2, 1500, date(2024, 11, 15))     # overpayment 200
        create_payment(cls.bill3, 1400, date(2025, 2, 15))
        # no payment for bill4, -1500
        create_payment(cls.bill5, 1500, date(2024, 10, 15))

    def test_member_balance(self):
        balances = get_memberbalances(date(2024, 12, 31))

        print(balances)

        self.assertEqual(len(balances), 2)
        self.assertEqual(balances[0]['first_name'], 'Alpha')
        self.assertEqual(balances[0]['last_name'], 'Member1')
        self.assertEqual(balances[0]['billed_amount'], 2500)
        self.assertEqual(balances[0]['paid_amount'], 2700)
        self.assertEqual(balances[0]['balance'], -200)

        self.assertEqual(balances[1]['first_name'], 'Beta')
        self.assertEqual(balances[1]['last_name'], 'Member2')
        self.assertEqual(balances[1]['billed_amount'], 3100)
        self.assertEqual(balances[1]['paid_amount'], 1500)
        self.assertEqual(balances[1]['balance'], 1600)
