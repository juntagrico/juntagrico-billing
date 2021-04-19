from datetime import date

from django.utils.translation import gettext as _

from juntagrico_billing.dao.billdao import BillDao
from juntagrico_billing.dao.paymentdao import PaymentDao
from juntagrico_billing.dao.subscriptions import subscriptions_by_date
from juntagrico_billing.entity.settings import Settings
from juntagrico_billing.util.billing import scale_subscription_price

# Offset for generating Document numbers for bookings
DOCNUMBER_OFFSET_BILL = 500000
DOCNUMBER_OFFSET_PAYMENT = 600000


class Booking(object):
    pass


def subscription_bookings_by_date(fromdate, tilldate):
    """
    Generate a list of booking for subscriptions.
    For each type that is assigned to a subscription, a separate booking
    is generated.
    """
    subscriptions = subscriptions_by_date(fromdate, tilldate)

    # global debtor account on settings object
    debtor_account = Settings.objects.first().debtor_account

    bookings = []
    for subs in subscriptions:
        for subs_part in subs.parts.all():
            booking = Booking()
            booking.date = max(fromdate, subs.activation_date or date.min)
            booking.activation_date = subs.activation_date
            booking.deactivation_date = subs.deactivation_date
            booking.docnumber = gen_document_number(subs, fromdate)
            booking.member = subs.primary_member
            booking.text = "Abo: %s, %s" % (subs_part.type, subs.primary_member)
            eff_start = max(fromdate, subs.activation_date or date.min)
            eff_end = min(tilldate, subs.deactivation_date or date.max)
            if (eff_start > fromdate) or (eff_end < tilldate):
                # subscription is activated or deactivate inside our interval
                # set special marker price and mention interval in text
                booking.price = 0.99
                booking.text = "%s, Teilperiode %s - %s" % (booking.text,
                                                            eff_start.strftime("%d.%m.%y"),
                                                            eff_end.strftime("%d.%m.%y"))
            else:
                booking.price = scale_subscription_price(subs, fromdate, tilldate)
                # accounts
            booking.debit_account = debtor_account  # soll: debitor-konto
            if hasattr(subs_part.type, "subscriptiontype_account"):
                booking.credit_account = subs_part.type.subscriptiontype_account.account
            else:
                booking.credit_account = ""
            if hasattr(subs.primary_member, "member_account"):
                booking.member_account = subs.primary_member.member_account.account
            else:
                booking.member_account = ""

            bookings.append(booking)
    return bookings


def gen_document_number(entry, range_start):
    """
    Generate document number for booking a suscription or extra subscription.
    The generated document number is affected by the start-date of the booking period, so
    that each subscription gets a unique document number per booking period.

    Structure of document number:
    YYMMDD<id of primary member 9-digits><id of subcription 9-digits>

    If no member is assigned, the member part is all 0.
    """
    date_part = range_start.strftime('%y%m%d')
    if hasattr(entry, 'primary_member'):
        member = entry.primary_member
    else:
        member = entry.main_subscription.primary_member
    if member:
        member_id = str(member.id)
    else:
        member_id = ""
    member_part = member_id.rjust(9, '0')
    entry_part = str(entry.id).rjust(9, '0')
    return date_part + member_part + entry_part


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
    if item.subscription_type:
        if hasattr(item.subscription_type, "subscriptiontype_account"):
            booking.credit_account = item.subscription_type.subscriptiontype_account.account
        else:
            booking.credit_account = ""

    elif item.extrasubscription_type:
        category = item.extrasubscription_type.category
        if hasattr(category, "extrasub_account"):
            booking.credit_account = category.extrasub_account.account
        else:
            booking.credit_account = ""
    elif item.custom_item_type:
        booking.credit_account = item.custom_item_type.booking_account

    # docnumber is DOCNUMBER_OFFSET_BILL + id of bill*10 + sequencenumber of bill item
    booking.docnumber = str(DOCNUMBER_OFFSET_BILL + bill.id * 10 + idx + 1)

    # "Bl" is short form for "Bill"
    booking.text = "%s %d: %s %s" % (_('Bl'), bill.id, item.item_kind, bill.member)
    booking.debit_account = debtor_account
    booking.price = item.amount
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

    return bookings
