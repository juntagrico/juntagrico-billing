from datetime import date

from django.core.exceptions import ValidationError
from django.urls import reverse
from juntagrico.entity.subs import SubscriptionPart

from juntagrico_billing.models.bill import Bill, BillItemType
from juntagrico_billing.util.billing import cancel_bills, restore_bills, \
    create_bill, get_billable_subscription_parts, get_open_bills, \
    get_unpublished_bills, get_memberbalances, publish_bills, recalc_bill
from juntagrico_billing.util.bookings import get_bill_bookings
from . import BillingTestCase


class CancelBillsTest(BillingTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.item_type = BillItemType.objects.create(name='Test Item Type', booking_account='2211')

        # an unpublished bill, as generated for the business year
        cls.unpublished_bill = create_bill(
            cls.subscription.parts.all(), cls.year, cls.year.start_date)

        # a published bill of another member
        cls.published_bill = cls.create_bill(
            cls.member2, cls.item_type, date(2018, 3, 1), 500.0)

    def test_cancel_bill(self):
        cancel_bills([self.unpublished_bill.id])

        self.unpublished_bill.refresh_from_db()
        self.assertTrue(self.unpublished_bill.cancelled)

    def test_restore_bill(self):
        cancel_bills([self.unpublished_bill.id])
        restore_bills([self.unpublished_bill.id])

        self.unpublished_bill.refresh_from_db()
        self.assertFalse(self.unpublished_bill.cancelled)

    def test_cancel_bill_with_payment(self):
        """
        bills with payments can not be cancelled,
        they are returned by cancel_bills.
        """
        self.create_payment(self.payment_type, self.published_bill, 500.0, date(2018, 4, 1))

        not_cancelled = cancel_bills([self.published_bill.id])

        self.assertEqual([self.published_bill], not_cancelled)
        self.published_bill.refresh_from_db()
        self.assertFalse(self.published_bill.cancelled)

    def test_validation_of_cancelled_bill_with_payment(self):
        self.create_payment(self.payment_type, self.published_bill, 500.0, date(2018, 4, 1))

        self.published_bill.cancelled = True
        with self.assertRaises(ValidationError):
            self.published_bill.full_clean()

    def test_cancelled_bill_not_unpublished(self):
        self.assertIn(self.unpublished_bill, get_unpublished_bills())

        cancel_bills([self.unpublished_bill.id])
        self.assertNotIn(self.unpublished_bill, get_unpublished_bills())

    def test_cancelled_bill_not_open(self):
        self.assertIn(self.published_bill, get_open_bills(self.year, 100))

        cancel_bills([self.published_bill.id])
        self.assertNotIn(self.published_bill, get_open_bills(self.year, 100))

    def test_cancelled_bill_not_published(self):
        """
        publishing a cancelled bill has no effect.
        """
        cancel_bills([self.unpublished_bill.id])
        publish_bills([self.unpublished_bill.id])

        self.unpublished_bill.refresh_from_db()
        self.assertFalse(self.unpublished_bill.published)

    def test_cancelled_bill_not_visible_to_member(self):
        bills = Bill.objects.of_member(self.member2).published().active()
        self.assertIn(self.published_bill, bills)

        cancel_bills([self.published_bill.id])
        bills = Bill.objects.of_member(self.member2).published().active()
        self.assertNotIn(self.published_bill, bills)

    def test_cancelled_bill_has_no_bookings(self):
        bookings = get_bill_bookings(self.year.start_date, self.year.end_date)
        self.assertEqual(2, len(bookings), 'bookings of both bills')

        cancel_bills([self.unpublished_bill.id])

        bookings = get_bill_bookings(self.year.start_date, self.year.end_date)
        self.assertEqual(1, len(bookings), 'only bookings of the remaining bill')

    def test_cancelled_bill_not_in_memberbalance(self):
        def balances_of_member2():
            return [balance for balance in get_memberbalances(self.year.end_date)
                    if balance['id'] == self.member2.id]

        balances = balances_of_member2()
        self.assertEqual(1, len(balances))
        self.assertEqual(500.0, balances[0]['billed_amount'])

        cancel_bills([self.published_bill.id])

        self.assertEqual(0, len(balances_of_member2()))

    def test_parts_of_cancelled_bill_stay_billed(self):
        """
        the subscription parts of a cancelled bill are not billable again,
        i.e. they don't show up as pending bills.
        this is how trial subscriptions or mid-year joins are
        permanently excluded from billing.
        """
        billable_parts = get_billable_subscription_parts(self.year)
        self.assertNotIn(self.part, billable_parts, 'part is on the unpublished bill')

        cancel_bills([self.unpublished_bill.id])

        billable_parts = get_billable_subscription_parts(self.year)
        self.assertNotIn(self.part, billable_parts, 'part stays billed after cancelling')

    def test_cancelled_bill_blocks_recalc_of_other_bill(self):
        """
        a part on a cancelled bill is not moved to another bill by recalc.
        """
        extra_part = SubscriptionPart.objects.create(
            subscription=self.subscription,
            activation_date=date(2018, 1, 1),
            type=self.extrasub_type
        )
        other_bill = create_bill([extra_part], self.year, self.year.start_date)
        cancel_bills([self.unpublished_bill.id])

        recalc_bill(other_bill)

        parts = [itm.subscription_part for itm in other_bill.items.all()]
        self.assertNotIn(self.part, parts)


class CancelBillsViewTest(BillingTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.item_type = BillItemType.objects.create(name='Test Item Type', booking_account='2211')
        cls.bill = cls.create_bill(cls.member2, cls.item_type, date(2018, 3, 1), 500.0)

    def test_bills_cancel(self):
        self.assertGet(reverse('jb:bills-cancel'), 302)
        self.assertGet(reverse('jb:bills-cancel'), 405, member=self.admin)
        self.assertPost(reverse('jb:bills-cancel'), {'bill_ids': str(self.bill.id)},
                        code=302, member=self.admin)

        self.bill.refresh_from_db()
        self.assertTrue(self.bill.cancelled)

    def test_cancelled_bill_not_visible_in_user_view(self):
        self.assertGet(reverse('jb:user-bill', args=[self.bill.id]), member=self.member2)

        cancel_bills([self.bill.id])

        self.assertGet(reverse('jb:user-bill', args=[self.bill.id]), 403, member=self.member2)
        self.assertGet(reverse('jb:user-bill-pdf', args=[self.bill.id]), 403, member=self.member2)
        # the bookkeeper can still see it
        self.assertGet(reverse('jb:user-bill', args=[self.bill.id]), member=self.admin)
