from datetime import date, timedelta
from django.utils import timezone

from juntagrico.dao.subscriptiondao import SubscriptionDao
from juntagrico.dao.extrasubbillingperioddao import ExtraSubBillingPeriodDao
from juntagrico.util.temporal import start_of_next_business_year, end_of_business_year
from juntagrico.util.temporal import start_of_specific_business_year
from juntagrico.util.temporal import end_of_specific_business_year
from juntagrico.util.temporal import start_of_business_year
from juntagrico.config import Config

from juntagrico_billing.entity.bill import Bill
from juntagrico_billing.entity.bill import BusinessYear
from juntagrico_billing.mailer import send_bill_sub, send_bill_share, send_bill_extrasub

type_codes = {'subscription': '01', 'share': '02', 'extra': '03'}


def calculate_check_number(ref_number):
    numbers = [0, 9, 4, 6, 8, 2, 7, 1, 3, 5]
    overfloat = 0
    for n in ref_number:
        overfloat = numbers[(overfloat+int(n)) % 10]
    return str((10-overfloat) % 10)


def generate_ref_number(type, billable_id, recipient_id, start=None):
    type_code = type_codes.get(type, '00')
    start_code = '000000'
    if start is not None:
        start_code = start.strftime('%y%m%d')
    billable_code = str(billable_id).rjust(9, '0')
    recipient_code = str(recipient_id).rjust(9, '0')
    without_cs = type_code+billable_code+recipient_code+start_code
    cs = calculate_check_number(without_cs)
    return without_cs+cs


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
            result.append(part.type.price +days_part/days_period)

    return sum(result)


def get_billable_subscriptions(business_year):
    """
    get all subscriptions that are active during the given period and
    don't have a corresponding bill.
    """
    from_date = business_year.start_date
    till_date = business_year.end_year

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
