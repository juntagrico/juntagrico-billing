from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.utils.translation import gettext as _
from juntagrico.entity.subs import SubscriptionPart
from django.contrib.messages import error
from django.db.models import Sum, Q

from juntagrico.util.xls import generate_excel
from juntagrico.entity.member import Member
from juntagrico_billing.models.bill import Bill, BillItem
from juntagrico_billing.models.payment import Payment
from juntagrico_billing.models.settings import Settings


def scale_subscriptionpart_price(part, fromdate, tilldate):
    """
    scale subscription part price for a certain date interval.
    """

    if part.type.periods.count():
        # calculate price based on billing periods.
        # takes into account periods that overlap with the requested interval.
        period_prices = []
        for period in part.type.periods.all():
            period_start = date(fromdate.year, period.start_month, period.start_day)
            period_end = date(fromdate.year, period.end_month, period.end_day)
            if period_start <= tilldate and period_end >= fromdate:
                # calculate the resulting start and end of the period that overlaps
                # with the activation date and our requested date interval
                eff_start = max(fromdate, max(period_start, part.activation_date or date.min))
                eff_end = min(tilldate, min(period_end, part.deactivation_date or date.max))

                # scale the period price
                full_days = (period_end - period_start).days + 1
                eff_days = (eff_end - eff_start).days + 1

                period_prices.append(period.price * Decimal(eff_days / full_days))

        # round to .05
        return round(Decimal(2.0) * sum(period_prices), 1) / Decimal('2.0')

    # otherwise
    # calculate price without billing periods.
    # just scale the subscription type price proportionately
    days_period = (tilldate - fromdate).days + 1
    if part.activation_date and part.activation_date <= tilldate:
        part_start = max(part.activation_date or date.min, fromdate)
        part_end = min(part.deactivation_date or date.max, tilldate)
        days_part = (part_end - part_start).days + 1
        return round(part.type.price * Decimal(2.0 * days_part / days_period), 1) / Decimal('2.0')

    return 0


def get_billable_subscription_parts(business_year):
    """
    get all subscription parts that are active during the given period and
    don't have a corresponding bill.
    """
    from_date = business_year.start_date
    till_date = business_year.end_date

    # prepare a dictionary with member, subscription_part tuples as keys
    # based on the bills of this year
    bill_items = BillItem.objects.filter(bill__business_year=business_year)
    bill_parts = [itm.subscription_part for itm in bill_items if itm.subscription_part]

    # get all active subscription parts for billing period
    active_parts = SubscriptionPart.objects.in_daterange(from_date, till_date)

    # get parts that are not billed yet
    billed_dict = dict([(part, None) for part in bill_parts])

    not_billed = [part for part in active_parts if part not in billed_dict]

    return not_billed


def update_bill_parts(bill, subscription_parts):
    """
    update a bill with the given subscription parts.
    all existing parts will be removed and replaced by the new ones.
    """
    # remove existing subscription part items
    for itm in bill.items.all():
        if itm.subscription_part:
            itm.delete()

    for part in subscription_parts:
        price = scale_subscriptionpart_price(
            part,
            bill.business_year.start_date,
            bill.business_year.end_date)
        text = str(part.type)
        bill_item = BillItem.objects.create(
            bill=bill, subscription_part=part,
            amount=float(price), description=text)
        # vat amount is calculated on save
        bill_item.save()

    # set total amount on bill
    bill.amount = sum([itm.amount for itm in bill.items.all()])
    bill.save()


def create_bill(billable_items, businessyear, bill_date, vat_rate=0.0):
    booking_date = max(businessyear.start_date, bill_date)

    # make sure all billables belong to the same member
    billables_per_member = group_billables_by_member(billable_items)
    if len(billables_per_member) > 1:
        raise Exception('billable items belong to different members')

    # create bill for member
    member = list(billables_per_member.keys())[0]
    bill = Bill.objects.create(business_year=businessyear, amount=0.0, member=member,
                               bill_date=bill_date, booking_date=booking_date,
                               vat_rate=vat_rate)

    update_bill_parts(bill, billable_items)
    return bill


def recalc_bill(bill):
    """
    update an existing bill with all items that are not
    on another bill in the same businessyear.
    """
    # get all subscription parts for member and businessyear
    year = bill.business_year
    member = bill.member
    parts_in_year = SubscriptionPart.objects.by_primary_member(member).in_daterange(year.start_date, year.end_date)

    # determine if part is on another bill in the same year
    def is_on_other_bill(part):
        items = part.bill_items.all()
        for itm in items:
            if itm.bill:
                if itm.bill != bill:
                    if itm.bill.business_year == year:
                        return True
        return False

    parts = [part for part in parts_in_year
             if not is_on_other_bill(part)]

    update_bill_parts(bill, parts)


def group_billables_by_member(billable_items):
    """
    returns a dictionary grouping the billable subscription parts
    per member.
    """
    # group the subscription parts per member
    parts_per_member = defaultdict(list)

    for part in billable_items:
        if part.subscription.primary_member:
            parts_per_member[part.subscription.primary_member].append(part)

    return parts_per_member


def create_bills_for_items(billable_items, businessyear, bill_date):
    """
    Create bills based on a list of subscriptions and extrasubscriptions.
    Creates a bill per member and adding the subscriptions and extrasubscriptions
    """
    # get current vat percentage from settings
    vat_rate = round(Settings.objects.first().vat_percent / 100, 4)

    # get dictionary of billables per member
    items_per_member = group_billables_by_member(billable_items)

    # create a bill per member
    bills = []
    for items in items_per_member.values():
        bills.append(create_bill(items, businessyear, bill_date, vat_rate))

    return bills


def get_open_bills(businessyear, expected_percentage_paid):
    """
    get unpaid bills from a businessyear, filtering on unpaid amount.
    bills are considered open, if the percentage of paid amount is less
    than the given expected percentage.
    """
    # fetch unpaid bills, SQL filtered
    unpaid_bills = businessyear.bills.filter(paid=False, published=True)

    return [
        bill for bill in unpaid_bills
        if (bill.amount > 0) and (bill.amount_paid / bill.amount * 100.0 < expected_percentage_paid)]


def get_unpublished_bills():
    """
    get bills not published yet (no visible to members).
    """
    return Bill.objects.filter(published=False)


def publish_bills(id_list):
    """
    Publishes a set of bills given by their ids.
    """
    for bill_id in id_list:
        bill = Bill.objects.get(pk=bill_id)
        bill.published = True
        bill.save()


def update_vat(bill):
    """
    update the vat amount on a bill.
    """
    # get the current vat rate from settings
    bill.vat_rate = round(Settings.objects.first().vat_percent / 100, 4)
    bill.save()

    # update the vat amount on all items
    for itm in bill.items.all():
        itm.save()


def add_balancing_payment(request, bill):
    """
    balance bill by adding a compensation payment (usually solidarity fund contribution)
    """
    # get the payment type from settings
    balancing_paymenttype = Settings.objects.first().balancing_paymenttype
    if not balancing_paymenttype:
        error(request, _("No balancing payment type configured."))
        return

    # add a payment to balance the bill
    if bill.amount_open:
        payment = Payment.objects.create(bill=bill, amount=bill.amount_open,
                                         paid_date=date.today(),
                                         type=balancing_paymenttype)
        payment.save()
        bill.paid = True
        bill.save()


def get_memberbalances(keydate):
    """
    get member balances for a given date.
    """
    members_billed_amount = Member.objects.annotate(
        billed_amount=Sum('bills__amount', filter=Q(bills__booking_date__lte=keydate)),
        ).filter(billed_amount__gt=0).values('id', 'first_name', 'last_name', 'billed_amount')
    members_paid_amount = Member.objects.annotate(
        paid_amount=Sum('bills__payments__amount', filter=Q(bills__payments__paid_date__lte=keydate)),
        ).filter(paid_amount__gt=0).values('id', 'first_name', 'last_name', 'paid_amount')

    member_dict = {}
    for member in members_billed_amount:
        member_dict[member['id']] = member

    for member in members_paid_amount:
        if member['id'] in member_dict:
            member_dict[member['id']].update(member)

    for member in member_dict.values():
        member['balance'] = member.get('billed_amount', 0) - member.get('paid_amount', 0)

    return sorted(member_dict.values(), key=lambda x: x['last_name'])


def export_memberbalance_sheet(request, keydate):
    """
    Export a member balance sheet for a given date.
    """
    fields = {
        'last_name': 'Nachname',
        'first_name': 'Vorname',
        'billed_amount': 'Rechnungen',
        'paid_amount': 'Zahlungen',
        'balance': 'Saldo'
    }

    filename = 'memberbalances_{}.xlsx'.format(keydate)
    lines = get_memberbalances(keydate)

    return generate_excel(fields.items(), lines, filename)
