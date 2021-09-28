from juntagrico.entity.subs import Subscription, SubscriptionPart


def subscription_parts_by_date(fromdate, tilldate):
    """
    subscription parts that are active in a certain period.
    all subscription parts except those that ended before or
    started after our date range.
    """
    return SubscriptionPart.objects\
        .exclude(activation_date__isnull=True)\
        .exclude(deactivation_date__lt=fromdate)\
        .exclude(activation_date__gt=tilldate)


def subscription_parts_member_date(member_id, fromdate, tilldate):
    """
    subscription parts for a certain member
    that are active in a period.
    """
    return SubscriptionPart.objects\
        .filter(subscription__primary_member=member_id)\
        .exclude(activation_date__isnull=True)\
        .exclude(deactivation_date__lt=fromdate)\
        .exclude(activation_date__gt=tilldate)


def subscriptions_by_date(fromdate, tilldate):
    """
    subscriptions that are active in a certain period
    all subscriptions except those that ended before or
    started after our date range.
    """
    return Subscription.objects.exclude(activation_date__isnull=True).\
        exclude(deactivation_date__lt=fromdate).exclude(
            activation_date__gt=tilldate)
