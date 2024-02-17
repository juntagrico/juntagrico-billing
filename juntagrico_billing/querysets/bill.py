from django.db import models


class BillQuerySet(models.QuerySet):
    def of_member(self, member):
        return self.filter(member=member)

    def published(self):
        return self.filter(published=True)

    def in_daterange(self, from_date, till_date):
        return self.filter(booking_date__gte=from_date, booking_date__lte=till_date)


class BusinessYearQuerySet(models.QuerySet):
    def by_name(self, yearname):
        return self.filter(name=yearname).first()
