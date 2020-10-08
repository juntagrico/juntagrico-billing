from juntagrico_billing.entity.bill import Bill, BusinessYear


class BillDao:

    @staticmethod
    def bills_for_billables(billables):
        return Bill.objects.filter(billable__in=billables)

    @staticmethod
    def businessyear_by_name(yearname):
        return BusinessYear.objects.filter(name=yearname).first()
