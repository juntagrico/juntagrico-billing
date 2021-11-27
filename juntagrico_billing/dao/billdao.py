from juntagrico_billing.entity.bill import Bill, BusinessYear


class BillDao:

    @staticmethod
    def bills_for_member(member):
        return Bill.objects.filter(member=member, published=True)

    @staticmethod
    def bills_for_daterange(fromdate, tilldate):
        return Bill.objects.filter(
            booking_date__gte=fromdate,
            booking_date__lte=tilldate)

    @staticmethod
    def businessyear_by_name(yearname):
        return BusinessYear.objects.filter(name=yearname).first()
