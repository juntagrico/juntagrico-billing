from django.db import models


class PaymentQuerySet(models.QuerySet):

    def in_daterange(self, from_date, till_date):
        return self.filter(paid_date__gte=from_date, paid_date__lte=till_date)
