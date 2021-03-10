from juntagrico_billing.entity.payment import Payment


class PaymentDao:

    @staticmethod
    def payments_for_daterange(fromdate, tilldate):
        return Payment.objects.filter(
            paid_date__gte=fromdate,
            paid_date__lte=tilldate)
