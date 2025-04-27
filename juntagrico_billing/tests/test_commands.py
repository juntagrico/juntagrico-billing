from io import StringIO

from django.core.management import call_command

from juntagrico.tests import JuntagricoTestCase


class ManagementCommandsTest(JuntagricoTestCase):
    def test_generate_testdata(self):
        out = StringIO()
        call_command('generate_billing_testdata', stdout=out)
        self.assertEqual(out.getvalue(), '')
