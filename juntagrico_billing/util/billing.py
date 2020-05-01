from datetime import date

from juntagrico.dao.extrasubbillingperioddao import ExtraSubBillingPeriodDao
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
            result.append(part.type.price * days_part/days_period)

    return sum(result)


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
    # TODO fix extra price
    price = 1

    return create_bill(e_sub, businessyear, date, price)
