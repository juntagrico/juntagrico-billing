from datetime import date
from decimal import Decimal

from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.urls import reverse
from juntagrico.entity.subs import SubscriptionSurcharge

from . import BillingTestCase
from ..admin.billitem_inline import BillItemInline
from ..models.bill import BillItem, BillItemType
from ..util.billing import (
    create_bill, create_bills_for_items, get_billable_items,
    get_billable_surcharges, recalc_bill,
)
from ..util.bookings import get_bill_bookings
from ..util.pdfbill import PdfBillRenderer


class SurchargeTests(BillingTestCase):
    def surcharge(self, amount='50.25', billing_date=date(2018, 6, 1), description='Contribution'):
        return SubscriptionSurcharge.objects.create(
            subscription=self.subscription, date=billing_date,
            amount=Decimal(amount), description=description,
        )

    def test_billable_dates_amount_and_existing_bill(self):
        first = self.surcharge(billing_date=self.year.start_date)
        last = self.surcharge(amount='-10', billing_date=self.year.end_date)
        self.surcharge(billing_date=date(2017, 12, 31))
        next_year = self.surcharge(billing_date=date(2019, 1, 1))
        self.surcharge(amount='0')
        self.assertCountEqual(get_billable_surcharges(self.year), [first, last])

        bill = create_bill([first], self.year, self.year.start_date)
        self.assertCountEqual(get_billable_surcharges(self.year), [last])
        other_year = self.create_business_year(2019)
        BillItem.objects.create(bill=bill, surcharge=last, amount=-10)
        last.date = other_year.start_date
        last.save()
        self.assertCountEqual(get_billable_surcharges(other_year), [last, next_year])

    def test_create_and_recalculate(self):
        surcharge = self.surcharge(description='x' * 255)
        bills = create_bills_for_items(get_billable_items(self.year), self.year, self.year.start_date)
        bill = next(bill for bill in bills if bill.member == self.subscription.primary_member)
        item = bill.items.get(surcharge=surcharge)
        self.assertEqual(item.amount, 50.25)
        self.assertEqual(str(item), 'x' * 255)
        self.assertEqual(bill.amount, 1250.25)
        self.assertEqual(list(bill.ordered_items)[-1], item)
        self.assertNotIn(surcharge, get_billable_surcharges(self.year))

        custom = BillItem.objects.create(
            bill=bill, custom_item_type=BillItemType.objects.create(name='Other', booking_account='1'),
            amount=10,
        )
        surcharge.amount = Decimal('75.00')
        surcharge.save()
        recalc_bill(bill)
        bill.refresh_from_db()
        self.assertEqual(bill.amount, 1285)
        self.assertTrue(bill.items.filter(pk=custom.pk).exists())
        self.assertEqual(bill.items.get(surcharge=surcharge).amount, 75)
        recalc_bill(bill)
        self.assertEqual(bill.items.filter(surcharge=surcharge).count(), 1)

    def test_recalculate_does_not_duplicate_another_bill(self):
        surcharge = self.surcharge()
        first_bill = create_bill([self.part], self.year, self.year.start_date)
        second_bill = create_bill([surcharge], self.year, self.year.start_date)
        recalc_bill(first_bill)
        self.assertFalse(first_bill.items.filter(surcharge=surcharge).exists())
        recalc_bill(second_bill)
        self.assertEqual(second_bill.items.filter(surcharge=surcharge).count(), 1)

    def test_surcharge_only_preview_generation_and_pdf(self):
        part_bill = create_bill([self.part], self.year, self.year.start_date)
        surcharge = self.surcharge(description='Contribution < & >')
        self.client.force_login(self.admin.user)
        session = self.client.session
        session['bills_businessyear'] = '2018'
        session.save()
        response = self.client.get(reverse('jb:pending-bills-list'))
        self.assertContains(response, '50,25')
        self.assertContains(response, 'Surcharge')
        self.assertEqual(self.client.post(reverse('jb:bills-generate')).status_code, 302)
        item = BillItem.objects.get(surcharge=surcharge)
        self.assertNotEqual(item.bill, part_bill)
        self.assertEqual(item.bill.amount, 50.25)
        self.assertIn(str(self.subscription.id), str(BillItemInline.item_kind_link(None, item)))
        PdfBillRenderer().render(item.bill, HttpResponse())

    def test_surcharge_account_positive_and_negative(self):
        self.settings.surcharge_account = '3050'
        self.settings.save()
        positive = self.surcharge()
        negative = self.surcharge(amount='-20', description='Discount')
        create_bill([positive, negative], self.year, self.year.start_date)
        bookings = get_bill_bookings(self.year.start_date, self.year.end_date)
        self.assertEqual((bookings[0].debit_account, bookings[0].credit_account, bookings[0].price),
                         ('1100', '3050', 50.25))
        self.assertEqual((bookings[1].debit_account, bookings[1].credit_account, bookings[1].price),
                         ('3050', '1100', 20))

    def test_bill_item_rejects_multiple_sources(self):
        surcharge = self.surcharge()
        bill = create_bill([surcharge], self.year, self.year.start_date)
        item = bill.items.get()
        item.custom_item_type = BillItemType.objects.create(name='Other', booking_account='1')
        with self.assertRaises(ValidationError):
            item.full_clean()
