from juntagrico_billing.entity.payment import Payment


class PaymentDao:

    @staticmethod
    def payments_for_daterange(fromdate, tilldate):
        return Payment.objects.filter(
            paid_date__gte=fromdate,
            paid_date__lte=tilldate)

    @staticmethod
    def exists_payment_with_unique_id(unique_id):
        return Payment.objects.filter(unique_id=unique_id).count()
