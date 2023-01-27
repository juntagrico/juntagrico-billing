from collections import defaultdict
from datetime import date
from decimal import Decimal

from juntagrico_billing.dao.subscription_parts import\
    subscription_parts_by_date, subscription_parts_member_date
from juntagrico_billing.entity.bill import Bill, BillItem
from juntagrico_billing.entity.settings import Settings


def scale_subscriptionpart_price(part, fromdate, tilldate):
    """
    scale subscription part price for a certain date interval.
    """

    if len(part.type.periods.all()):
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
    active_parts = subscription_parts_by_date(from_date, till_date)

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
    parts_in_year = subscription_parts_member_date(
        member, year.start_date, year.end_date)

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
        parts_per_member[part.subscription.primary_member].append(part)

    return parts_per_member


def create_bills_for_items(billable_items, businessyear, bill_date):
    """
    Create bills based on a list of subscriptions and extrasubscriptions.
    Creates a bill per member and adding the subscriptions and extrasubscriptions
    """
    # get current vat percentage from settings
    vat_rate = Settings.objects.first().vat_percent / 100

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
