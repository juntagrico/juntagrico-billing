from datetime import date
from collections import defaultdict

from juntagrico.dao.extrasubscriptiondao import ExtraSubscriptionDao
from juntagrico.dao.subscriptiondao import SubscriptionDao
from juntagrico.entity.subs import Subscription, SubscriptionPart
from juntagrico.entity.extrasubs import ExtraSubscription
from juntagrico_billing.entity.bill import Bill, BillItem
from juntagrico_billing.dao.subscriptions import subscriptions_by_date, extrasubscriptions_by_date


def scale_subscription_price(subscription, fromdate, tilldate):
    """
    scale subscription price for a certain date interval.
    """
    result = []
    for part in subscription.parts.all():
        result.append(scale_subscriptionpart_price(part, fromdate, tilldate))

    return sum(result)


def scale_subscriptionpart_price(part, fromdate, tilldate):
    """
    scale subscription part price for a certain date interval.
    """
    days_period = (tilldate - fromdate).days + 1
    if part.activation_date and part.activation_date <= tilldate:
        part_start = max(part.activation_date or date.min, fromdate)
        part_end = min(part.deactivation_date or date.max, tilldate)
        days_part = (part_end - part_start).days + 1
        return round(part.type.price * days_part / days_period, 2)

    return 0


def scale_extrasubscription_price(extrasub, fromdate, tilldate):
    """
    calculate price of an extrasubscription for a certain date intverval.
    takes into account periods that overlap with the requested interval.
    """
    period_prices = []
    for period in extrasub.type.periods.all():
        period_start = date(fromdate.year, period.start_month, period.start_day)
        period_end = date(fromdate.year, period.end_month, period.end_day)
        if period_start <= tilldate and period_end >= fromdate:
            # calculate the resulting start and end of the period that overlaps
            # with the activation date and our requested date interval
            eff_start = max(fromdate, max(period_start, extrasub.activation_date or date.min))
            eff_end = min(tilldate, min(period_end, extrasub.deactivation_date or date.max))

            # scale the period price
            full_days = (period_end - period_start).days + 1
            eff_days = (eff_end - eff_start).days + 1

            period_prices.append(float(period.price) * eff_days / full_days)

    return round(sum(period_prices), 2)


def get_billable_items(business_year):
    """
    get all billable items that are active during the given period and
    don't have a corresponding bill.
    Billable items are either SubscriptionPart or Extrasubscription objects
    """
    from_date = business_year.start_date
    till_date = business_year.end_date

    # prepare a dictionary with member, billable_reference tuples as keys
    # based on the bills of this year
    # billable_references are either subscription types and extrasubscription types
    bill_items = BillItem.objects.filter(bill__business_year=business_year)
    already_billed = dict((((itm.bill.member, itm.billable_reference), None) for itm in bill_items))

    # get all active subscriptions and extra subscriptions that overlap our date range
    subscriptions = subscriptions_by_date(from_date, till_date)
    # todo: change to get subscription parts directly
    subscription_parts = [part for sub in subscriptions for part in sub.parts.all()]
    extra_subs = extrasubscriptions_by_date(from_date, till_date)

    # check if we have a member for every billable
    parts_without_member = [part for part in subscription_parts if not part.subscription.primary_member]
    es_without_member = [es for es in extra_subs if not es.main_subscription.primary_member]
    if parts_without_member:
        raise Exception('SubscriptionPart without member: %s' % parts_without_member[0])

    if es_without_member:
        raise Exception('ExtraSubscription without member: %s' % es_without_member[0])

    # check if they already have a bill with billing date in the date range
    result_list = [part for part in subscription_parts if (part.subscription.primary_member, part.type) not in already_billed] + \
                  [es for es in extra_subs if (es.main_subscription.primary_member, es.type) not in already_billed]

    return result_list


def create_bill(billable_items, businessyear, bill_date):
    booking_date = max(businessyear.start_date, bill_date)

    # make sure all billables belong to the same member
    billables_per_member = group_billables_by_member(billable_items)
    if len(billables_per_member) > 1:
        raise Exception('billable items belong to different members')

    # create bill for member
    member = list(billables_per_member.keys())[0]
    bill = Bill.objects.create(business_year=businessyear, amount=0.0, member=member,
                               bill_date=bill_date, booking_date=booking_date)

    items = []
    for billable in billable_items:
        if isinstance(billable, SubscriptionPart):
            # subscription part
            part = billable
            price = scale_subscriptionpart_price(part, businessyear.start_date, businessyear.end_date)
            text = str(part.type)
            bill_item = BillItem.objects.create(bill=bill, subscription_type=part.type,
                                                amount=price, description=text)
            bill_item.save()
            items.append(bill_item)
        elif isinstance(billable, ExtraSubscription):
            # extra subscription
            price = scale_extrasubscription_price(billable,
                                                  businessyear.start_date, businessyear.end_date)
            text = str(billable.type)
            bill_item = BillItem.objects.create(bill=bill, extrasubscription_type=billable.type,
                                                amount=price, description=text)
            bill_item.save()
            items.append(bill_item)

        # set total amount on bill
        bill.amount = sum([itm.amount for itm in items])

    bill.save()
    return bill


def group_billables_by_member(billable_items):
    """
    returns a dictionary grouping the billable items (SubscriptionPart or Extrasubscriptions)
    per member.
    """
    # group the items per member
    items_per_member = defaultdict(list)

    for item in billable_items:
        if isinstance(item, SubscriptionPart):
            items_per_member[item.subscription.primary_member].append(item)
        elif isinstance(item, ExtraSubscription):
            items_per_member[item.main_subscription.primary_member].append(item)
        else:
            raise Exception('unsupported item for bill: %s' % repr(item))

    return items_per_member


def create_bills_for_items(billable_items, businessyear, bill_date):
    """
    Create bills based on a list of subscriptions and extrasubscriptions.
    Creates a bill per member and adding the subscriptions and extrasubscriptions
    """
    # get dictionary of billables per member
    items_per_member = group_billables_by_member(billable_items)

    # create a bill per member
    bills = []
    for items in items_per_member.values():
        bills.append(create_bill(items, businessyear, bill_date))

    return bills


def get_open_bills(businessyear, expected_percentage_paid):
    """
    get unpaid bills from a businessyear, filtering on unpaid amount.
    bills are considered open, if the percentage of paid amount is less
    than the given expected percentage.
    """
    # fetch unpaid bills, SQL filtered
    unpaid_bills = businessyear.bills.filter(paid=False)

    return [bill for bill in unpaid_bills
            if bill.amount_paid / bill.amount * 100.0 < expected_percentage_paid]


