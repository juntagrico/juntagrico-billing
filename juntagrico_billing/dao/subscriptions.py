from juntagrico.entity.subs import Subscription
from juntagrico.entity.extrasubs import ExtraSubscription


def subscriptions_by_date(fromdate, tilldate):
    """
    subscriptions that are active in a certain period
    all subscriptions except those that ended before or
    started after our date range.
    """
    return Subscription.objects.exclude(activation_date__isnull=True).\
        exclude(deactivation_date__lt=fromdate).exclude(
            activation_date__gt=tilldate)


def extrasubscriptions_by_date(fromdate, tilldate):
    """
    subscriptions that are active in a certain period.
    all subscriptions except those that ended before or
    started after the date range.
    """
    return ExtraSubscription.objects.exclude(activation_date__isnull=True).\
        exclude(deactivation_date__lt=fromdate).\
        exclude(activation_date__gt=tilldate)
