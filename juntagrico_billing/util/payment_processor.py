from juntagrico.entity.member import Member
from juntagrico_billing.entity.payment import Payment, PaymentType
from juntagrico_billing.entity.bill import Bill
from juntagrico_billing.util.qrbill import bill_id_from_refnumber, member_id_from_refnumber

class PaymentInfo(object):
    def __init__(self, date, credit_iban, amount, ref_type, reference, id):
        self.date = date
        self.credit_iban = credit_iban
        self.amount = amount
        self.ref_type = ref_type
        self.reference = reference
        self.id = id

    def __repr__(self):
        return 'PaymentInfo %s %.2f %s %s' % (
                self.date, self.amount, self.reference, self.id)


class PaymentProcessorError(Exception):
    pass


class PaymentProcessor(object):
    def __init__(self):
        # initialize a dictionary of iban numbers and
        # corresponding payment types
        self.payment_types = dict(
            [(pt.iban, pt) for pt in PaymentType.objects.all()])


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
          - invalid billing reference and no open bill for same member
          - invalid bill and member reference
          - the credit account was not found              
        """
        if not self.find_paymenttype(paymentinfo):
            raise PaymentProcessorError('Payment for account iban %s can not be imported, because there is no paymenttype for this account.' % \
                        paymentinfo.credit_iban)

        member = self.find_member(paymentinfo)
        if not member:
            raise PaymentProcessorError('Payment from member %d can not be imported, because there is no member with this id.' % \
                        member_id_from_refnumber(paymentinfo.reference))

        bill = self.find_bill(paymentinfo)
        if bill and (bill.member == member):
            return ('OK', bill)

        # consider the most recent open bill of the same member
        bills = member.bills.filter(paid=False).order_by('-bill_date')
        if len(bills):
            return ('OTHER_BILL', bills[0])
        
        raise PaymentProcessorError('Payment from member %d can not be imported, because there is no open bill for the member.' % \
                        member.id)


    def find_bill(self, paymentinfo):
        """
        find bill by id from reference number
        """
        bill_id = bill_id_from_refnumber(paymentinfo.reference)

        try:
            return Bill.objects.get(id=bill_id)
        except:
            return None


    def find_member(self, paymentinfo):
        """
        find member by id from reference number
        """
        member_id = member_id_from_refnumber(paymentinfo.reference)

        try:
            return Member.objects.get(id=member_id)
        except:
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
        self.import_payments([(bill, payments[idx]) for idx, (code, bill) in enumerate(check_results)])


    def import_payments(self, bills_and_payments):
        """
        when import_payments is called, all the payments 
        should be importable and associateable to the given bill.
        """
        for bill, pinfo in bills_and_payments:
            payment = Payment.objects.create(
                        bill=bill,
                        type=self.find_paymenttype(pinfo),
                        paid_date=pinfo.date,
                        amount=pinfo.amount)
            payment.save()

