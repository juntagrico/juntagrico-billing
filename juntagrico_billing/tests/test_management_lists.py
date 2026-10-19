from datetime import date

from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from . import BillingTestCase
from ..models.bill import BillItemType


class ManagementListTests(BillingTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # create some bills
        cls.item_type1 = BillItemType.objects.create(name='Test Item Type', booking_account='2211')
        cls.bill1 = cls.create_bill(cls.member2, cls.item_type1, date(2024, 10, 1), 1200)
        cls.bill2 = cls.create_bill(cls.member2, cls.item_type1, date(2024, 11, 1), 1300)

    def test_open_bills(self):
        self.assertGet(reverse('jb:open-bills-list'), 302)
        self.assertGet(reverse('jb:open-bills-list'), member=self.admin)

    def test_pending_bills(self):
        self.assertGet(reverse('jb:pending-bills-list'), 302)
        self.assertGet(reverse('jb:pending-bills-list'), member=self.admin)

    def test_unpublished_bills(self):
        self.assertGet(reverse('jb:unpublished-bills-list'), 302)
        self.assertGet(reverse('jb:unpublished-bills-list'), member=self.admin)

    def test_bills_publish(self):
        self.assertGet(reverse('jb:bills-publish'), 302)
        self.assertGet(reverse('jb:bills-publish'), 405, member=self.admin)
        self.assertPost(reverse('jb:bills-publish'), {'bill_ids': str(self.bill1.id)}, code=302, member=self.admin)

    def test_bills_set_year(self):
        self.assertGet(reverse('jb:bills-setyear'), 302)
        self.assertPost(reverse('jb:bills-setyear'), {'year': 2017}, 302)
        self.assertIsNone(self.client.session.get('bills_businessyear'))

        self.assertGet(reverse('jb:bills-setyear'), 405, member=self.admin)
        self.assertPost(reverse('jb:bills-setyear'), {'year': 2017}, 302, member=self.admin)
        self.assertEqual(self.client.session.get('bills_businessyear'), '2017')

    def test_bills_generate(self):
        self.assertGet(reverse('jb:bills-generate'), 302)
        self.assertPost(reverse('jb:bills-generate'), code=302)

        self.client.force_login(self.admin.user)
        session = self.client.session
        session['bills_businessyear'] = '2018'
        session.save()
        self.assertGet(reverse('jb:bills-generate'), 405, member=self.admin)
        self.assertPost(reverse('jb:bills-generate'), code=302, member=self.admin)

    def test_bills_notify(self):
        self.assertGet(reverse('jb:bills-notify'), 302)
        self.assertGet(reverse('jb:bills-notify'), member=self.admin)

    def test_invalid_bill_ids_are_ignored(self):
        self.bill1.published = False
        self.bill1.save()
        for data in ({}, {'bill_ids': ''}, {'bill_ids': 'abc_1x_'}):
            self.assertPost(reverse('jb:bills-publish'), data, code=302, member=self.admin)
            self.assertPost(reverse('jb:bills-notify'), data, code=302, member=self.admin)
        self.bill1.refresh_from_db()
        self.assertFalse(self.bill1.published)
        self.assertFalse(self.bill1.notification_sent)

    def test_bills_generate_without_year(self):
        response = self.assertPost(reverse('jb:bills-generate'), code=302, member=self.admin)
        self.assertEqual(response.url, reverse('jb:pending-bills-list'))

    def test_unknown_year_in_session(self):
        self.assertPost(reverse('jb:bills-setyear'), {'year': 'unknown'}, 302, member=self.admin)
        self.assertGet(reverse('jb:pending-bills-list'), member=self.admin)
        self.assertGet(reverse('jb:open-bills-list'), member=self.admin)
        # falls back to the most recent year
        self.assertEqual(self.client.session.get('bills_businessyear'), self.year.name)

    def test_bills_recalc(self):
        self.assertGet(reverse('jb:bill-recalc', args=[1]) + '?next=.', 302)
        self.assertGet(reverse('jb:bill-recalc', args=[1]) + '?next=.', 302, member=self.admin)

    def test_accounting_summary(self):
        self.assertGet(reverse('jb:accounting-summary'), 302)
        self.assertGet(reverse('jb:accounting-summary'), member=self.admin)

    def test_payments_upload_invalid_file(self):
        upload = SimpleUploadedFile('payments.xml', b'this is not a camt.054 file')
        response = self.assertPost(reverse('jb:payments-upload'), {'file': upload}, code=302, member=self.admin)
        self.assertEqual(response.url, reverse('jb:payments-upload'))
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any('payments.xml' in m for m in messages), messages)
