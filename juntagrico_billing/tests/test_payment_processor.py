import unittest
from datetime import date

from django import test

from juntagrico_billing.models.bill import Bill
from juntagrico_billing.models.payment import Payment, PaymentType
from juntagrico_billing.util.qrbill import bill_id_from_refnumber, member_id_from_refnumber
from juntagrico_billing.util.payment_processor import PaymentProcessor, PaymentInfo, PaymentProcessorError
from . import BillingTestCase


class ReferenceNumberTest(unittest.TestCase):
    def test_bill_id_from_refnumber(self):
        self.assertEqual(
            1234,
            bill_id_from_refnumber('000001000000567800000012344'))
        self.assertEqual(
            1234567890,
            bill_id_from_refnumber('000001000000567812345678909'))

    def test_member_id_from_refnumber(self):
        self.assertEqual(
            5678,
            member_id_from_refnumber('000001000000567800000012344'))
        self.assertEqual(
            2345678901,
            member_id_from_refnumber('000001234567890112345678902'))


class PaymentProcessorTest(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.businessyear = BillingTestCase.create_business_year()
        # create member and businessyear
        cls.member = BillingTestCase.create_billing_member('Peter', 'Tester')

        # create 2 paymenttypes
        cls.paymenttype1 = PaymentType.objects.create(
            name="QR Account",
            iban="CH7730000001250094239"
        )
        cls.paymenttype2 = PaymentType.objects.create(
            name="Other Account",
            iban="CH2909000000250094239"
        )

        # create 2 bills for member
        bill_date1 = cls.businessyear.start_date
        cls.bill1 = Bill.objects.create(
            business_year=cls.businessyear, amount=0.0,
            member=cls.member,
            bill_date=bill_date1, booking_date=bill_date1
        )
        bill_date2 = date(2018, 4, 25)
        cls.bill2 = Bill.objects.create(
            business_year=cls.businessyear,
            amount=0.0, member=cls.member,
            bill_date=bill_date2, booking_date=bill_date2
        )

        cls.processor = PaymentProcessor(testing=True)

    def test_check_payment_ok(self):
        """
        test paymentinfo that is valid for importing.
        """
        pinfo = PaymentInfo(
            date(2018, 3, 15),
            'CH7730000001250094239',
            250.0,
            'QRR',
            '000000000000000100000000010',
            'xa56-klkw345'
        )

        code, bill = self.processor.check_payment(pinfo)
        self.assertEqual('OK', code)
        self.assertEqual(self.bill1, bill)

    def test_check_payment_other_bill(self):
        """
        test payment with invalid bill reference where
        other bill can be found.
        """
        pinfo = PaymentInfo(
            date(2018, 3, 15),
            'CH7730000001250094239',
            250.0,
            'QRR',
            '000000000000000100000000052',
            'xa56-klkw345'
        )

        code, bill = self.processor.check_payment(pinfo)
        self.assertEqual('OTHER_BILL', code)
        self.assertEqual(self.bill2, bill)

    def test_check_payment_no_bill(self):
        """
        test payment with invalid bill reference where
        no other open bill can be found.
        """
        # set the 2 bills to paid
        self.bill1.paid = True
        self.bill1.save()
        self.bill2.paid = True
        self.bill2.save()

        pinfo = PaymentInfo(
            date(2018, 3, 15),
            'CH7730000001250094239',
            250.0,
            'QRR',
            '000000000000000100000000052',
            'xa56-klkw345'
        )

        with self.assertRaisesMessage(
                PaymentProcessorError,
                'Payment from member 1 can not be imported, because there is no open bill for the member.'):
            self.processor.check_payment(pinfo)

    def test_check_payment_no_member(self):
        """
        test payment with invalid bill and member reference
        """
        pinfo = PaymentInfo(
            date(2018, 3, 15),
            'CH7730000001250094239',
            250.0,
            'QRR',
            '000000000000000300000000051',
            'xa56-klkw345'
        )

        with self.assertRaisesMessage(
                PaymentProcessorError,
                'Payment from member 3 can not be imported, because there is no member with this id.'):
            self.processor.check_payment(pinfo)

    def test_check_payment_no_account(self):
        """
        test payment with invalid iban
        """
        pinfo = PaymentInfo(
            date(2018, 3, 15),
            'CH7730000001230094239',
            250.0,
            'QRR',
            '000000000000000300000000051',
            'xa56-klkw345'
        )

        with self.assertRaisesMessage(
                PaymentProcessorError,
                'Payment for account iban CH7730000001230094239 can not be imported, because there is no paymenttype for this account.'):
            self.processor.check_payment(pinfo)

    def test_check_payment_exists(self):
        """
        test payment that already exists
        """
        # create an existing payment
        payment = Payment.objects.create(
            bill=self.bill1,
            type=self.paymenttype1,
            paid_date=date(2018, 3, 1),
            amount=10.0,
            unique_id='5x81cd67')
        payment.save()

        pinfo = PaymentInfo(
            date(2018, 3, 15),
            'CH7730000001250094239',
            250.0,
            'QRR',
            '000000000000000100000000010',
            '5x81cd67'
        )

        with self.assertRaisesMessage(
                PaymentProcessorError,
                'Payment with unique id 5x81cd67 has already been imported.'):
            self.processor.process_payments([pinfo])

    def test_process_payments_ok(self):
        """
        process 2 payments that are OK
        """
        payment_infos = []

        pinfo = PaymentInfo(
            date(2018, 3, 15),
            'CH7730000001250094239',
            250.0,
            'QRR',
            '000000000000000100000000010',
            'xa56-klkw345'
        )
        payment_infos.append(pinfo)

        pinfo = PaymentInfo(
            date(2018, 3, 16),
            'CH7730000001250094239',
            210.0,
            'QRR',
            '000000000000000100000000021',
            'xa56-klkw789'
        )
        payment_infos.append(pinfo)

        self.processor.process_payments(payment_infos)

        # check if payments assigned
        self.assertEquals(1, len(self.bill1.payments.all()))
        self.assertEquals(
            date(2018, 3, 15),
            self.bill1.payments.all()[0].paid_date)
        self.assertEquals(250.0, self.bill1.payments.all()[0].amount)

        self.assertEquals(1, len(self.bill2.payments.all()))
        self.assertEquals(
            date(2018, 3, 16),
            self.bill2.payments.all()[0].paid_date)
        self.assertEquals(210.0, self.bill2.payments.all()[0].amount)

    def test_process_payments_failed(self):
        """
        process 2 payments that are not OK
        the first one is OK, the second one has wrong member.
        """
        payment_infos = []

        pinfo = PaymentInfo(
            date(2018, 3, 15),
            'CH7730000001250094239',
            250.0,
            'QRR',
            '000000000000000100000000010',
            'xa56-klkw345'
        )
        payment_infos.append(pinfo)

        pinfo = PaymentInfo(
            date(2018, 3, 16),
            'CH7730000001250094239',
            210.0,
            'QRR',
            '000000000000000300000000027',
            'xa56-klkw789'
        )
        payment_infos.append(pinfo)

        with self.assertRaisesMessage(
                PaymentProcessorError,
                'Payment from member 3 can not be imported, because there is no member with this id.'):
            self.processor.process_payments(payment_infos)

        # check that no payments are assigned
        self.assertEquals(0, len(self.bill1.payments.all()))
        self.assertEquals(0, len(self.bill2.payments.all()))
