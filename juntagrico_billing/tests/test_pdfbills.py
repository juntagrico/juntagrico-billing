from datetime import date

from django.http import HttpResponse
from juntagrico.entity.subs import SubscriptionPart

from juntagrico_billing.util.billing import create_bill
from . import BillingTestCase
from ..util.pdfbill import PdfBillRenderer


class PdfBillTests(BillingTestCase):
    def test_pdf_bill(self):
        bill = create_bill(self.subscription.parts.all(), self.year, self.year.start_date)
        PdfBillRenderer().render(bill, HttpResponse())

    def test_zero_amount_pdf_bill(self):
        self.extrasubs = SubscriptionPart.objects.create(
            subscription=self.subscription,
            activation_date=date(2018, 1, 1),
            type=self.sub_type3
        )
        bill = create_bill(self.subscription.parts.all(), self.year, self.year.start_date)
        PdfBillRenderer().render(bill, HttpResponse())
