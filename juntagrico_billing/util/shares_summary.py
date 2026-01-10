from juntagrico.entity.share import Share
from django.db.models import Sum
from decimal import Decimal

def get_shares_summary(start_date, end_date):
    """
    Get a summary of share paid and paid back between start_date and end_date,
    with balances at start_date and end_date.
    """
    shares = Share.objects.all()

    start_paid = shares.filter(paid_date__lt=start_date).aggregate(total=Sum('value'))['total'] or Decimal('0.0')
    start_paid_back = shares.filter(payback_date__lt=start_date).aggregate(total=Sum('value'))['total'] or Decimal('0.0')
    start_balance = start_paid - start_paid_back

    end_paid = shares.filter(paid_date__lte=end_date).aggregate(total=Sum('value'))['total'] or Decimal('0.0')
    end_paid_back = shares.filter(payback_date__lte=end_date).aggregate(total=Sum('value'))['total'] or Decimal('0.0')
    end_balance = end_paid - end_paid_back

    return {
        'range_balance': end_balance - start_balance,
        'start_balance': start_balance,
        'end_balance': end_balance,
    }