from datetime import date

from juntagrico.dao.extrasubscriptiondao import ExtraSubscriptionDao
from juntagrico.dao.subscriptiondao import SubscriptionDao

from juntagrico_billing.entity.bill import Bill


def scale_subscription_price(subscription, fromdate, tilldate):
    """
    scale subscription price for a certain date interval.
    """
    result = []
    days_period = (tilldate - fromdate).days + 1
    for part in subscription.parts.all():
        if part.activation_date and part.activation_date <= tilldate:
            part_start = max(part.activation_date or date.min, fromdate)
            part_end = min(part.deactivation_date or date.max, tilldate)
            days_part = (part_end - part_start).days + 1
            result.append(part.type.price * days_part / days_period)

    return round(sum(result), 2)


def scale_extrasubscription_price(extrasub, fromdate, tilldate):
    """
    calculate price of an extrasubscription for a certain date intverval.
    takes into account periods that overlap with the requested interval.
    """
    period_prices = []
    for period in extrasub.type.periods.all():
        period_start = date(fromdate.year, period.start_month, period.start_day)
        period_end = date(fromdate.year, period.end_month, period.end_day)
        if (period_start > tilldate) or (period_end < fromdate):
            # skip periods outside our interval
            continue

        # calculate the resulting start and end of the period that overlaps
        # with the activation date and our requested date interval
        eff_start = max(fromdate, max(period_start, extrasub.activation_date or date.min))
        eff_end = min(tilldate, min(period_end, extrasub.deactivation_date or date.max))

        # scale the period price
        full_days = (period_end - period_start).days + 1
        eff_days = (eff_end - eff_start).days + 1

        period_prices.append(period.price * eff_days / full_days)

    return round(sum(period_prices), 2)


def get_billable_subscriptions(business_year):
    """
    get all subscriptions that are active during the given period and
    don't have a corresponding bill.
    """
    from_date = business_year.start_date
    till_date = business_year.end_date

    # get all active subscriptions and extra subscriptions that overlap our date range
    subscriptions = SubscriptionDao.subscriptions_by_date(from_date, till_date)
    extra_subs = ExtraSubscriptionDao.extrasubscriptions_by_date(from_date, till_date)

    # get all bills with bill_date in our date range
    bills = business_year.bills.all()
    bills_by_subs = [bill.billable for bill in bills]

    # check if they already have a bill with billing date in the date range
    result_list = [sub for sub in subscriptions if sub not in bills_by_subs] + \
                  [e_sub for e_sub in extra_subs if e_sub not in bills_by_subs]

    return result_list


def create_bill(billable, businessyear, date, amount):
    bill = Bill.objects.create(billable=billable,
                               business_year=businessyear,
                               amount=amount,
                               bill_date=date)
    return bill


def create_subscription_bill(subscription, businessyear, date):
    """
    create a bill for a subscription and a businessyear.
    """
    price = scale_subscription_price(subscription,
                                     businessyear.start_date, businessyear.end_date)

    return create_bill(subscription, businessyear, date, price)


def create_extra_sub_bill(e_sub, businessyear, date):
    """
    create a bill for a extra subscription and a businessyear.
    """
    price = scale_extrasubscription_price(e_sub,
                                          businessyear.start_date, businessyear.end_date)

    return create_bill(e_sub, businessyear, date, price)
