from datetime import date

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
            result.append(part.type.price * days_part/days_period)

    return sum(result)


def get_billable_subscriptions(business_year):
    """
    get all subscriptions that are active during the given period and
    don't have a corresponding bill.
    """
    from_date = business_year.start_date
    till_date = business_year.end_date

    # get all active subscriptions that overlap our date range
    subscriptions = SubscriptionDao.subscriptions_by_date(from_date, till_date)

    # get all bills with bill_date in our date range
    bills = business_year.bills.all()
    bills_by_subs = [bill.billable for bill in bills]

    # check if they already have a bill with billing date in the date range
    result_list = []
    for sub in subscriptions:
        if sub in bills_by_subs:
            continue
        result_list.append(sub)
    
    return result_list


def create_subscription_bill(subscription, businessyear, date):
    """
    create a bill for a subscription and a businessyear.
    """
    price = scale_subscription_price(subscription,
                                     businessyear.start_date, businessyear.end_date)

    bill = Bill.objects.create(billable=subscription,
                               business_year=businessyear,
                               amount=price,
                               bill_date=date)
    return bill
