from datetime import date

from django.urls import reverse

from . import BillingTestCase
from ..models.bill import BillItemType
from ..models.settings import Settings


class UserBillsTests(BillingTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.item_type = BillItemType.objects.create(name='Test Item Type', booking_account='2211')
        cls.bill = cls.create_bill(cls.member, cls.item_type, date(2018, 10, 1), 1200)

    def test_user_bills(self):
        self.assertGet(reverse('jb:user-bills'))

    def test_user_bills_loads_datatables(self):
        response = self.assertGet(reverse('jb:user-bills'))
        self.assertContains(response, 'juntagrico/external/datatables/datatables.min.js')

    def test_user_bills_column_count(self):
        """
        DataTables refuses to initialize if the number of header cells
        does not match the number of cells per row.
        """
        html = self.assertGet(reverse('jb:user-bills')).content.decode()
        header = html.split('<thead>')[1].split('</thead>')[0]
        first_row = html.split('<tbody>')[1].split('</tr>')[0]
        self.assertEqual(header.count('<th'), first_row.count('<td'))

    def test_user_bill(self):
        self.assertGet(reverse('jb:user-bill', args=[self.bill.id]))

    def test_user_bill_unpublished(self):
        """
        members can not see their own bills before they are published,
        bookkeepers can.
        """
        self.bill.published = False
        self.bill.save()
        self.assertGet(reverse('jb:user-bill', args=[self.bill.id]), 403)
        self.assertGet(reverse('jb:user-bill-pdf', args=[self.bill.id]), 403)
        self.assertGet(reverse('jb:user-bill', args=[self.bill.id]), member=self.admin)
        self.assertGet(reverse('jb:user-bill-pdf', args=[self.bill.id]), member=self.admin)

    def test_user_bill_of_other_member(self):
        self.assertGet(reverse('jb:user-bill', args=[self.bill.id]), 403, member=self.member2)
        self.assertGet(reverse('jb:user-bill-pdf', args=[self.bill.id]), 403, member=self.member2)

    def test_user_bills_without_settings(self):
        """
        the bill list must render even if the bookkeeping settings
        have not been created yet.
        """
        Settings.objects.all().delete()
        self.assertGet(reverse('jb:user-bills'))

    def test_user_bill_without_settings(self):
        """
        a single bill must render even if the bookkeeping settings
        have not been created yet. No payment part is shown then.
        """
        Settings.objects.all().delete()
        response = self.assertGet(reverse('jb:user-bill', args=[self.bill.id]))
        self.assertNotContains(response, 'IBAN')

    def test_user_bill_without_default_paymenttype(self):
        """
        the default payment type is optional, an unset one must not
        break the bill view either.
        """
        self.settings.default_paymenttype = None
        self.settings.save()
        response = self.assertGet(reverse('jb:user-bill', args=[self.bill.id]))
        self.assertNotContains(response, 'IBAN')
