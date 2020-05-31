from juntagrico_billing.entity.bill import Bill


class BillDao:

    @staticmethod
    def bills_for_billables(billables):
        return Bill.objects.filter(billable__in=billables)
