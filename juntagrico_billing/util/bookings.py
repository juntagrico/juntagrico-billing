from django.utils.translation import gettext as _

from juntagrico_billing.dao.billdao import BillDao
from juntagrico_billing.dao.paymentdao import PaymentDao
from juntagrico_billing.entity.settings import Settings

# Offset for generating Document numbers for bookings
DOCNUMBER_OFFSET_BILL = 500000
DOCNUMBER_OFFSET_PAYMENT = 600000


class Booking(object):
    pass


def get_bill_bookings(fromdate, tilldate):
    # get all bills by business-year start, end

    bills = BillDao.bills_for_daterange(fromdate, tilldate)

    # global debtor account on settings object
    debtor_account = Settings.objects.first().debtor_account

    bookings = []

    for bill in bills:
        for idx, item in enumerate(bill.items.all()):
            bookings.append(create_item_booking(idx, item, debtor_account))

    return bookings


def create_item_booking(idx, item, debtor_account):
    booking = Booking()
    bill = item.bill

    booking.date = bill.booking_date
    booking.credit_account = ""
    if item.subscription_part:
        stype = item.subscription_part.type
        if hasattr(stype, "subscriptiontype_account"):
            booking.credit_account = stype.subscriptiontype_account.account
        else:
            booking.credit_account = ""

    elif item.custom_item_type:
        booking.credit_account = item.custom_item_type.booking_account

    # docnumber is DOCNUMBER_OFFSET_BILL + id of bill*10 + sequencenumber of bill item
    booking.docnumber = str(DOCNUMBER_OFFSET_BILL + bill.id * 10 + idx + 1)

    # "Bl" is short form for "Bill"
    booking.text = "%s %d: %s %s" % (_('Bl'), bill.id, item.item_kind, bill.member)
    booking.debit_account = debtor_account
    if item.amount >= 0:
        booking.price = item.amount
        booking.vat_amount = item.vat_amount
    else:
        # negative amount: exchange accounts and set positive amount
        booking.price = -item.amount
        booking.vat_amount = -item.vat_amount
        booking.debit_account = booking.credit_account
        booking.credit_account = debtor_account

    if hasattr(bill.member, "member_account"):
        booking.member_account = bill.member.member_account.account
    else:
        booking.member_account = ""

    return booking


def get_payment_bookings(fromdate, tilldate):
    payments = PaymentDao.payments_for_daterange(fromdate, tilldate)

    # global debtor account on settings object
    debtor_account = Settings.objects.first().debtor_account

    bookings = []

    for payment in payments:
        booking = Booking()
        bookings.append(booking)

        booking.date = payment.paid_date
        booking.credit_account = debtor_account

        # docnumber is DOCNUMBER_OFFSET_PAYMENT + of bill*10 + sequence number of bill item
        booking.docnumber = str(DOCNUMBER_OFFSET_PAYMENT + payment.id)

        bill = payment.bill
        # 'Pmt' and 'Bl' are short forms for payment and bill
        booking.text = "%s %s %d: %s %s" % (_('Pmt'), _('Bl'), bill.id, bill.item_kinds, bill.member)
        # todo where to get bank account from?
        booking.debit_account = payment.type.booking_account
        booking.price = payment.amount
        if hasattr(payment.bill.member, "member_account"):
            booking.member_account = payment.bill.member.member_account.account
        else:
            booking.member_account = ""

        booking.vat_amount = 0.0

    return bookings
