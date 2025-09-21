from datetime import date
from decimal import Decimal

from django.conf import settings
import django.core.mail
from juntagrico.entity.subs import SubscriptionPart

from juntagrico_billing.models.bill import Bill, BillItem, BillItemType
from juntagrico_billing.util.billing import get_billable_subscription_parts, \
    create_bill, create_bills_for_items, recalc_bill, publish_bills
from juntagrico_billing.util.billing import scale_subscriptionpart_price
from juntagrico_billing.util.billing import get_open_bills
from juntagrico_billing.util.qrbill import bill_id_from_refnumber, member_id_from_refnumber
from juntagrico_billing.mailer import send_bill_notification
from . import BillingTestCase


class ScaleSubscriptionPriceTest(BillingTestCase):
    def test_price_by_date_fullyear(self):
        start_date = date(2018, 1, 1)
        end_date = date(2018, 12, 31)
        price_fullyear = scale_subscriptionpart_price(
            self.part, start_date, end_date)
        self.assertEqual(Decimal('1200.0'), price_fullyear, "full year")

    def test_price_by_date_shifted_business_year(self):
        settings.BUSINESS_YEAR_START = {'day': 1, 'month': 7}
        try:
            start_date = date(2018, 7, 1)
            end_date = date(2019, 6, 30)
            price_fullyear = scale_subscriptionpart_price(
                self.part, start_date, end_date)
            self.assertEqual(Decimal('1200.0'), price_fullyear, "full year")
        finally:
            del settings.BUSINESS_YEAR_START

    def test_price_by_date_partial_subscription(self):
        self.subscription.activation_date = date(2018, 7, 1)
        self.subscription.deactivation_date = date(2018, 9, 30)
        self.subscription.cancellation_date = self.subscription.deactivation_date
        self.part.activation_date = date(2018, 7, 1)
        self.part.deactivation_date = date(2018, 9, 30)
        self.part.cancellation_date = self.part.deactivation_date
        self.part.save()
        start_date = date(2018, 1, 1)
        end_date = date(2018, 12, 31)
        price = scale_subscriptionpart_price(
            self.part, start_date, end_date)
        price_expected = round(Decimal(2.0 * 1200.0 * (31 + 31 + 30) / 365), 1) / Decimal('2.0')
        self.assertEqual(price_expected, price,
                         "quarter subscription over a year")


class ScaleExtraSubscriptionPriceTest(BillingTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.extrasubs = SubscriptionPart.objects.create(
            subscription=cls.subscription,
            activation_date=date(2018, 1, 1),
            type=cls.extrasub_type
        )

        # calcluate expected price
        first_part = round(
            Decimal(2.0 * (100.0 * (31 + 30 + 31 + 30) / (31 + 28 + 31 + 30 + 31 + 30))), 1) / Decimal('2.0')
        second_part = round(
            Decimal(2.0 * (200.0 * (31 + 31 + 30 + 31) / (31 + 31 + 30 + 31 + 30 + 31))), 1) / Decimal('2.0')
        cls.expected_price = first_part + second_part

    def test_full_year(self):
        start_date = date(2018, 1, 1)
        end_date = date(2018, 12, 31)

        price = scale_subscriptionpart_price(self.extrasubs, start_date, end_date)
        self.assertEqual(Decimal('300.0'), price, "full year")

    def test_first_half_year(self):
        # first half year is exactly 1. extrasub period
        start_date = date(2018, 1, 1)
        end_date = date(2018, 6, 30)

        price = scale_subscriptionpart_price(self.extrasubs, start_date, end_date)
        self.assertEqual(Decimal('100.00'), price, "first half year")

    def test_second_half_year(self):
        # second half year is exactly 2. extrasub period
        start_date = date(2018, 7, 1)
        end_date = date(2018, 12, 31)

        price = scale_subscriptionpart_price(self.extrasubs, start_date, end_date)
        self.assertEqual(Decimal('200.00'), price, "second half year")

    def test_partial_year(self):
        start_date = date(2018, 3, 1)
        end_date = date(2018, 10, 31)

        price = scale_subscriptionpart_price(self.extrasubs, start_date, end_date)
        self.assertEquals(self.expected_price, price, "partial year")

    def test_partial_active(self):
        # full year but partial active extrasubscription
        start_date = date(2018, 1, 1)
        end_date = date(2018, 12, 31)

        self.extrasubs.activation_date = date(2018, 3, 1)
        self.extrasubs.deactivation_date = date(2018, 10, 31)

        price = scale_subscriptionpart_price(self.extrasubs, start_date, end_date)
        self.assertEquals(self.expected_price, price, "partial active")


class BillSubscriptionsTests(BillingTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # create some additional subscriptions
        cls.subs2 = cls.create_subscription_and_member(cls.sub_type, date(2017, 1, 1), None, "Test2", "17321")
        cls.subs3 = cls.create_subscription_and_member(cls.sub_type, date(2018, 3, 1), None, "Test3", "17321")

        # add an extra subscription part to base subscription
        cls.extrasubs = SubscriptionPart.objects.create(
            subscription=cls.subscription,
            activation_date=date(2018, 1, 1),
            type=cls.extrasub_type
        )

    def test_get_billable_subscriptions_without_bills(self):
        billable_parts = get_billable_subscription_parts(self.year)
        self.assertTrue(billable_parts)

        # excpect 3 subscriptions and 1 extra
        self.assertEqual(4, len(billable_parts))
        subscription = billable_parts[0].subscription
        self.assertEqual('Test', subscription.primary_member.last_name)

    def test_get_billable_subscriptions(self):
        # create bill for subs2
        create_bill(self.subs2.parts.all(), self.year, self.year.start_date)

        billable_parts = get_billable_subscription_parts(self.year)
        self.assertTrue(billable_parts)

        # we expect 2 normal subscriptions and 1 extra
        self.assertEqual(3, len(billable_parts))
        subscription = billable_parts[0].subscription
        self.assertEqual('Test', subscription.primary_member.last_name)

    def test_create_bill_multiple_members(self):
        # creating a bill for billable items from different members
        # should result in an error
        billable_items = get_billable_subscription_parts(self.year)
        with self.assertRaisesMessage(Exception, 'billable items belong to different members'):
            create_bill(billable_items, self.year, self.year.start_date)

    def test_create_bill(self):
        billable_items = [self.subscription.parts.all()[0], self.extrasubs]
        bill = create_bill(billable_items, self.year, self.year.start_date)

        self.assertEquals(2, len(bill.items.all()))
        self.assertEquals('Abo, Zusatzabo', bill.item_kinds)

    def test_create_bill_for_all(self):
        billable_items = get_billable_subscription_parts(self.year)
        bills = create_bills_for_items(billable_items, self.year, self.year.start_date)

        self.assertEqual(3, len(bills))

        # there should be no billable items left
        billable_items = get_billable_subscription_parts(self.year)
        self.assertEqual(0, len(billable_items))

    def test_recalc_bill_no_changes(self):
        """
        test that recalc bill does not alter a bill, if nothing was changed.
        """
        billable_items = get_billable_subscription_parts(self.year)
        bills = create_bills_for_items(billable_items, self.year, self.year.start_date)

        bill = bills[0]
        amount = bill.amount
        part_count = len(bill.items.all())

        recalc_bill(bill)
        self.assertEqual(amount, bill.amount)
        self.assertEqual(part_count, len(bill.items.all()))

    def test_recalc_bill_remove_part(self):
        """
        remove a subscription part from a subscription
        and recalc bill
        """
        billable_items = get_billable_subscription_parts(self.year)
        bills = create_bills_for_items(billable_items, self.year, self.year.start_date)

        bill = bills[0]
        items = bill.items.all()
        org_amount = bill.amount
        self.assertEqual(2, len(items))
        self.assertEqual('Normal', items[0].subscription_part.type.name)
        self.assertEqual(1200.0, items[0].amount)
        self.assertEqual('Extra 1', items[1].subscription_part.type.name)
        self.assertEqual(300.0, items[1].amount)

        # remove Extra 1 part
        # need to first remove item that references the part to delete
        part = items[1].subscription_part
        items[1].delete()
        part.delete()

        # recalced bill should have only 1 item and 300.0 less amount
        recalc_bill(bill)
        items = bill.items.all()
        self.assertEqual(1, len(items))
        self.assertEqual(org_amount - 300.0, bill.amount)
        self.assertEqual('Normal', items[0].subscription_part.type.name)

    def test_recalc_bill_change_period(self):
        """
        change start date of subscription and
        recalc bill.
        """
        billable_items = get_billable_subscription_parts(self.year)
        bills = create_bills_for_items(billable_items, self.year, self.year.start_date)

        bill = bills[0]
        org_amount = bill.amount
        items = bill.items.all()
        extra_item = items[1]
        self.assertEqual(300.0, extra_item.amount)

        # change activation date from 2018, 1, 1 to 2018, 7, 1
        extra_item.subscription_part.activation_date = date(2018, 7, 1)
        extra_item.subscription_part.save()

        # recalc: amount should be 100.0 less
        # because first half year of extrasub is 100.0
        # second half ist 200.0
        recalc_bill(bill)
        self.assertEqual(org_amount - 100.0, bill.amount)


class GetBillableItemsTests(BillingTestCase):
    def test_inactive_subscription(self):
        items_before = get_billable_subscription_parts(self.year)
        # create subscription without activation date, only start_date
        self.create_subscription_and_member(self.sub_type, None, None, "Test2", "4322")
        # we expect no billable items because subscription is not active in 2018
        items = get_billable_subscription_parts(self.year)
        self.assertEqual(len(items_before), len(items), "expecting no items for additional inactive subscription")


class BillCustomItemsTest(BillingTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.item_type1 = BillItemType.objects.create(name='Custom Item 1', booking_account='2211')
        cls.item_type2 = BillItemType.objects.create(name='Custom Item 2', booking_account='2212')

    def test_subscription_with_custom_item(self):
        # create a subscription bill
        bill = create_bill(self.subscription.parts.all(), self.year, self.year.start_date)

        self.assertEquals(1, len(bill.items.all()))
        self.assertEquals(1200.0, bill.amount)

        # add 2 custom items
        item = BillItem(bill=bill, custom_item_type=self.item_type1,
                        description='some custom item 1', amount=110.0)
        item.save()
        item = BillItem(bill=bill, custom_item_type=self.item_type2,
                        amount=120.0)
        item.save()
        bill.save()

        # test items
        self.assertEquals(3, len(bill.items.all()))
        self.assertEquals(1430.0, bill.amount)
        item = bill.items.all()[1]
        self.assertEquals('Custom Item 1', item.item_kind)
        self.assertEquals('some custom item 1', item.description)
        self.assertEquals('Custom Item 1 some custom item 1', str(item))
        item = bill.items.all()[2]
        self.assertEquals('Custom Item 2', item.item_kind)
        self.assertEquals('', item.description)
        self.assertEquals('Custom Item 2', str(item))

        # test description
        description_lines = bill.description.split('\n')
        self.assertEquals('Custom Item 1 some custom item 1', description_lines[1])
        self.assertEquals('Custom Item 2', description_lines[2])

    def test_recalc_with_custom_items(self):
        # create a subscription bill
        bill = create_bill(self.subscription.parts.all(), self.year, self.year.start_date)

        # add custom item
        item = BillItem(bill=bill, custom_item_type=self.item_type1,
                        description='some custom item 1', amount=110.0)
        item.save()
        bill.save()

        # check items count and total amount
        self.assertEquals(2, len(bill.items.all()), "items before recalc")
        self.assertEquals(1310.0, bill.amount, "amount before recalc")

        # recalc bill, amount should stay the same
        recalc_bill(bill)
        self.assertEquals(2, len(bill.items.all()), "items after recalc")
        self.assertEquals(1310.0, bill.amount, "amount after recalc")


class BillsListTest(BillingTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.member = cls.create_billing_member("Test", "Bills List")

        cls.item_type1 = BillItemType.objects.create(name='Test Item Type', booking_account='2211')

        # create some bills
        cls.bill1 = Bill.objects.create(
            business_year=cls.year, member=cls.member, published=True,
            bill_date=date(2018, 2, 1), booking_date=date(2018, 2, 1),
        )
        BillItem.objects.create(
            bill=cls.bill1,
            custom_item_type=cls.item_type1,
            amount=200.0
        )

        cls.bill2 = Bill.objects.create(
            business_year=cls.year, member=cls.member, published=True,
            bill_date=date(2018, 3, 1), booking_date=date(2018, 3, 1),
        )

        # bill3 is not published yet
        cls.bill3 = Bill.objects.create(
            business_year=cls.year, member=cls.member,
            bill_date=date(2018, 5, 1), booking_date=date(2018, 5, 1),
        )

    def test_get_open_bills(self):
        """
        query open bills
        """
        # get bills that are published but not fully paid
        bills = get_open_bills(self.year, 100)
        self.assertEqual(1, len(bills), '1 open bill, not counting zero bill')

    def test_bills_for_member(self):
        """
        query bills displayed to members.
        this should only include published bills.
        """
        bills = Bill.objects.of_member(self.member).published()
        self.assertEqual(2, len(bills), '2 published bills')

    def test_publish_bills(self):
        """
        publish some bills by id.
        bill1 and bill2 are already published, bill 3 not.
        """
        # first query published bills, only 2 are published
        self.assertEqual(2, len(Bill.objects.filter(published=True)), "only 2 bills are published")

        id_list = [self.bill1.id, self.bill2.id, self.bill3.id]
        publish_bills(id_list)

        # query published bills from db
        self.assertEqual(3, len(Bill.objects.filter(published=True)), "all 3 bills are published")


class BillTest(BillingTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.item_type = BillItemType(name='Custom', booking_account='2211')
        cls.item_type.save()

        # add an extra subscription part to base subscription
        cls.extrasubs = SubscriptionPart.objects.create(
            subscription=cls.subscription,
            activation_date=date(2018, 1, 1),
            type=cls.extrasub_type
        )

        cls.bill = create_bill(
            cls.subscription.parts.all(),
            cls.year,
            cls.year.start_date,
            0.025
        )

        # add custom item
        item = BillItem.objects.create(
            bill=cls.bill,
            custom_item_type=cls.item_type,
            amount=200.0
        )
        item.save()
        cls.bill.save()

    def test_ordered_items(self):
        """
        test ordered_items property on bill.
        introduced on bugfix for items without reference.
        """
        # create a bill with subscription, extra subscription and
        # custom item

        # add an item without reference (should not happen)
        item = BillItem.objects.create(
            bill=self.bill,
            amount=100.0
        )
        item.save()

        # test the ordered_items property
        items = self.bill.ordered_items
        self.assertEqual(4, len(items), 'should be 4 items')
        self.assertEqual('Abo', items[0].item_kind)
        self.assertEqual('Zusatzabo', items[1].item_kind)
        self.assertEqual('Custom', items[2].item_kind)
        self.assertEqual('', items[3].item_kind)

    def test_vat_subscription(self):
        # the first item should be the subsription item
        # with price 1200.00
        item = self.bill.items.all()[0]
        self.assertEquals(1200.0, item.amount)

        # we expect VAT (2.5%) of 29.27
        self.assertEquals(29.27, item.vat_amount)

    def test_no_vat_customitem(self):
        # custom items should have no vat
        item = self.bill.items.all()[2]
        self.assertEquals(0.0, item.vat_amount)

    def test_no_vat(self):
        # create bill with 0% vat (inclusive)
        bill = create_bill(
            self.subscription.parts.all(),
            self.year, self.year.start_date,
            0)

        # the first item should be the subsription item
        # with amount 1200.00
        item = bill.items.all()[0]
        self.assertEquals(1200.0, item.amount)

        # we expect no VAT
        self.assertEquals(0.0, item.vat_amount)

    def test_vat_on_changed_item(self):
        # changing a subscription parts amount
        # should recalc the vat amount on the item
        item = self.bill.items.all()[0]

        # change the amount from 1200 to 2000
        item.amount = 2000.0
        item.save()

        self.assertEquals(48.78, item.vat_amount)

    def test_refnumber(self):
        refnumber = self.bill.refnumber
        self.assertEquals(27, len(refnumber))
        self.assertEquals(self.bill.member.id, member_id_from_refnumber(refnumber))
        self.assertEquals(self.bill.id, bill_id_from_refnumber(refnumber))

    def test_notification_email_has_no_refnumber(self):
        """
        send email notification with no qr iban
        unit tests use the locmem email backend
        which stores the mails in django.core.mail.outbox
        """
        send_bill_notification(self.bill)
        outbox = django.core.mail.outbox
        self.assertEquals(1, len(outbox))
        msg = outbox[0].body
        self.assertFalse('Referencenumber:' in msg)

    def test_notification_email_has_refnumber(self):
        """
        send email notification with qr iban
        unit tests use the locmem email backend
        which stores the mails in django.core.mail.outbox
        """
        self.payment_type.iban = 'CH7730000001250094239'  # this is a qr iban
        self.payment_type.save()
        send_bill_notification(self.bill)
        outbox = django.core.mail.outbox
        self.assertEquals(1, len(outbox))
        msg = outbox[0].body

        reftext = 'Referenznummer:  {}'.format(self.bill.refnumber)
        self.assertTrue(reftext in msg)
