from django.db import IntegrityError, transaction
from django.utils.translation import gettext
from juntagrico.entity.member import Member
from juntagrico_billing.entity.bill import Bill
from juntagrico_billing.entity.payment import Payment, PaymentType
from juntagrico_billing.util.qrbill import bill_id_from_refnumber
from juntagrico_billing.util.qrbill import member_id_from_refnumber


class PaymentInfo(object):
    def __init__(self, date, credit_iban, amount, ref_type,
                 reference, unique_id):
        self.date = date
        self.credit_iban = credit_iban
        self.amount = amount
        self.ref_type = ref_type
        self.reference = reference
        self.unique_id = unique_id

    def __repr__(self):
        return 'PaymentInfo %s %.2f %s %s' % (
            self.date, self.amount, self.reference, self.unique_id)


class PaymentProcessorError(Exception):
    pass


class PaymentProcessor(object):
    def __init__(self, testing=False):
        self.testing = testing
        # initialize a dictionary of iban numbers and
        # corresponding payment types
        self.payment_types = dict(
            [(pt.iban, pt) for pt in PaymentType.objects.all()])

    def _(self, text):
        """
        internal translation method.
        skip translation of error messages in unit tests.
        """
        if not self.testing:
            return gettext(text)
        return text

    def check_payment(self, paymentinfo):
        """
        check if payment is acceptable.
        returns a result code and a corresponding bill object

        possible result-codes:
          OK:           account and billing reference ok
          OTHER_BILL:   invalid bill reference, but
                        another open bill of the same member
                        was found found

        exceptions are raised in the following cases
          - the payment has already been imported
          - invalid billing reference and no open bill for same member
          - invalid bill and member reference
          - the credit account was not found
        """

        if not self.find_paymenttype(paymentinfo):
            msg = 'Payment for account iban %s can not be imported, because there is no paymenttype for this account.'
            raise PaymentProcessorError(
                self._(msg) % paymentinfo.credit_iban)

        member = self.find_member(paymentinfo)
        if not member:
            msg = 'Payment from member %d can not be imported, because there is no member with this id.'
            raise PaymentProcessorError(
                self._(msg) % member_id_from_refnumber(paymentinfo.reference))

        bill = self.find_bill(paymentinfo)
        if bill and (bill.member == member):
            return ('OK', bill)

        # consider the most recent open bill of the same member
        bills = member.bills.filter(paid=False).order_by('-bill_date')
        if len(bills):
            return ('OTHER_BILL', bills[0])

        msg = 'Payment from member %d can not be imported, because there is no open bill for the member.'
        raise PaymentProcessorError(
            self._(msg) % member.id)

    def find_bill(self, paymentinfo):
        """
        find bill by id from reference number
        """
        bill_id = bill_id_from_refnumber(paymentinfo.reference)

        try:
            return Bill.objects.get(id=bill_id)
        except Bill.DoesNotExist:
            return None

    def find_member(self, paymentinfo):
        """
        find member by id from reference number
        """
        member_id = member_id_from_refnumber(paymentinfo.reference)

        try:
            return Member.objects.get(id=member_id)
        except Member.DoesNotExist:
            return None

    def find_paymenttype(self, paymentinfo):
        return self.payment_types.get(paymentinfo.credit_iban, None)

    def process_payments(self, payments):
        """
        process a list of payments.

        first check all payments if they are importable.
        the payments are only imported if there are not fatal errors.
        """
        check_results = [self.check_payment(p) for p in payments]
        self.import_payments([
            (bill, payments[idx])
            for idx, (code, bill) in enumerate(check_results)])

    def import_payments(self, bills_and_payments):
        """
        when import_payments is called, all the payments
        should be importable and associateable to the given bill.
        we are checking the uniqueness of the imported payments via
        db constraint.
        therefore the importing needs to be inside
        a transaction.
        we import either all payments or none.
        """
        with transaction.atomic():
            for bill, pinfo in bills_and_payments:
                try:
                    payment = Payment.objects.create(
                        bill=bill,
                        type=self.find_paymenttype(pinfo),
                        paid_date=pinfo.date,
                        amount=pinfo.amount,
                        unique_id=pinfo.unique_id)
                    payment.save()
                except IntegrityError:
                    msg = 'Payment with unique id %s has already been imported.'
                    raise PaymentProcessorError(
                        self._(msg) % pinfo.unique_id)
