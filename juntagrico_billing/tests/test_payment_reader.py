from unittest import TestCase
import datetime
from os.path import join, dirname
from juntagrico_billing.util.payment_reader import Camt045Reader


class Camt054ReaderTest(TestCase):
    def read_file(self, filename):
        testdir = dirname(__file__)
        with open(join(testdir, filename)) as f:
            return f.read()

    def test_read_qrpayments(self):
        reader = Camt045Reader()

        payments = reader.parse_payments(
            self.read_file('camt054_testfile.xml'))

        self.assertEqual(2, len(payments))
        payment = payments[0]
        self.assertEqual(datetime.date(2020, 6, 18), payment.date)
        self.assertEqual('CH7730000001250094239', payment.credit_iban)
        self.assertEqual(778.29, payment.amount)
        self.assertEqual('QRR', payment.ref_type)
        self.assertEqual('539115429773825311971477453', payment.reference)
        self.assertEqual('1006265-25bbb3b1a', payment.unique_id)

        payment = payments[1]
        self.assertEqual(datetime.date(2020, 6, 18), payment.date)
        self.assertEqual('CH7730000001250094239', payment.credit_iban)
        self.assertEqual(913.93, payment.amount)
        self.assertEqual('QRR', payment.ref_type)
        self.assertEqual('662437765447746478179744715', payment.reference)
        self.assertEqual('1005970-70a75515', payment.unique_id)

    def test_read_qrpayments2(self):
        """
        Variant of camt054 file from postfinance.
        this one was obtained from postfinance testplatform.

        The difference is, that the creditor iban appears
        in a detail creditor account element (CdtAcct) instead of
        in a general NtryRef element.
        """
        reader = Camt045Reader()

        payments = reader.parse_payments(
            self.read_file('camt054_testfile2.xml'))

        self.assertEqual(1, len(payments))
        payment = payments[0]
        self.assertEqual(datetime.date(2021, 2, 5), payment.date)
        self.assertEqual('CH1230000001156196402', payment.credit_iban)
        self.assertEqual(1.0, payment.amount)
        self.assertEqual('QRR', payment.ref_type)
        self.assertEqual('000000000000014200000000566', payment.reference)
        self.assertEqual('INSTRID-01-01', payment.unique_id)

    def test_read_qrpayments3(self):
        """
        Variant of camt054 file from Alternative Bank Schweiz
        that doesn't have a InstrId element in Ntry/NtryDtls/TxDtls/Refs
        but instead a TxId that we use as unique_id.
        """
        reader = Camt045Reader()

        payments = reader.parse_payments(
            self.read_file('camt054_testfile3.xml'))

        self.assertEqual(2, len(payments))
        payment = payments[0]
        self.assertEqual(datetime.date(2023, 2, 2), payment.date)
        self.assertEqual('CH9030123039005810105', payment.credit_iban)
        self.assertEqual(1000.0, payment.amount)
        self.assertEqual('QRR', payment.ref_type)
        self.assertEqual('000000000000015000000000722', payment.reference)
        self.assertEqual('30201715663.0001', payment.unique_id)

        payment = payments[1]
        self.assertEqual(datetime.date(2023, 2, 3), payment.date)
        self.assertEqual('CH9030123039005810105', payment.credit_iban)
        self.assertEqual(1050.0, payment.amount)
        self.assertEqual('QRR', payment.ref_type)
        self.assertEqual('000000000000013600000000688', payment.reference)
        self.assertEqual('230202CH09TIF874', payment.unique_id)
