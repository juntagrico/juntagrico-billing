
from unittest import TestCase
from juntagrico_billing.util.bexio_exporter import BexioExporter
from juntagrico_billing.util.bookings import Booking


class BexioExporterTest(TestCase):
    """
    Unit tests for the BexioExporter class.
    """
    def setUp(self):
        """
        Initializes the BexioExporterTest with a mock API client.

        :param api_client: The mock API client to use for testing.
        """
        existing_bookings = [
            Booking(date="2023-01-01", docnumber="12345", text="Test Booking",
                    debit_account="1100", credit_account="3001", price=100.0, vat_amount=20.0),
            Booking(date="2023-01-02", docnumber="12346", text="Another Booking",
                    debit_account="1100", credit_account="3001", price=200.0, vat_amount=40.0),
            Booking(date="2023-01-03", docnumber="12347", text="Third Booking",
                    debit_account="1100", credit_account="3001", price=300.0, vat_amount=60.0)
        ]

        self.api_client = TestApiClient(existing_bookings)
        self.exporter = BexioExporter(self.api_client)

    def test_export_bookings_no_changes(self):
        """
        Tests the export_bookings method of the BexioExporter.
        """
        # Arrange
        bookings = [
            Booking(date="2023-01-01", docnumber="12345", text="Test Booking",
                    debit_account="1100", credit_account="3001", price=100.0, vat_amount=20.0),
            Booking(date="2023-01-02", docnumber="12346", text="Another Booking",
                    debit_account="1100", credit_account="3001", price=200.0, vat_amount=40.0),
            Booking(date="2023-01-03", docnumber="12347", text="Third Booking",
                    debit_account="1100", credit_account="3001", price=300.0, vat_amount=60.0)
        ]

        result, msg = self.exporter.export_bookings(bookings)

        # Assert
        self.assertEquals(len(self.api_client.created_bookings), 0)
        self.assertEquals(len(self.api_client.updated_bookings), 0)
        self.assertEquals(len(self.api_client.deleted_bookings), 0)

        self.assertTrue('updated' in result)
        self.assertTrue('created' in result)
        self.assertTrue('deleted' in result)
        self.assertEquals(result['updated'], 0)
        self.assertEquals(result['created'], 0)
        self.assertEquals(result['deleted'], 0)

    def test_export_bookings_with_update(self):
        """
        Tests the export_bookings method with changes in bookings.
        """
        # Arrange
        bookings = [
            Booking(date="2023-01-01", docnumber="12345", text="Test Booking",
                    debit_account="1100", credit_account="3001", price=150.0, vat_amount=20.0),
            Booking(date="2023-01-02", docnumber="12346", text="Another Booking",
                    debit_account="1100", credit_account="3001", price=200.0, vat_amount=40.0),
            Booking(date="2023-01-03", docnumber="12347", text="Third Booking",
                    debit_account="1100", credit_account="3001", price=350.0, vat_amount=60.0)
        ]

        # Act
        result, msg = self.exporter.export_bookings(bookings)

        # Assert
        self.assertEquals(len(self.api_client.created_bookings), 0)
        self.assertEquals(len(self.api_client.updated_bookings), 2)  # Two bookings were updated
        self.assertEquals(len(self.api_client.deleted_bookings), 0)

        self.assertEquals(self.api_client.updated_bookings[0][1].price, 150.0)
        self.assertEquals(self.api_client.updated_bookings[1][1].price, 350.0)

        self.assertEquals(result['updated'], 2)
        self.assertEquals(result['created'], 0)
        self.assertEquals(result['deleted'], 0)

    def test_export_bookings_with_addition(self):
        """
        Tests the export_bookings method with a new booking addition.
        """
        bookings = [
            Booking(date="2023-01-01", docnumber="12345", text="Test Booking",
                    debit_account="1100", credit_account="3001", price=100.0, vat_amount=20.0),
            Booking(date="2023-01-02", docnumber="12346", text="Another Booking",
                    debit_account="1100", credit_account="3001", price=200.0, vat_amount=40.0),
            Booking(date="2023-01-03", docnumber="12347", text="Third Booking",
                    debit_account="1100", credit_account="3001", price=300.0, vat_amount=60.0),
            Booking(date="2023-01-04", docnumber="12348", text="Fourth Booking",
                    debit_account="1100", credit_account="3001", price=400.0, vat_amount=80.0)
        ]

        result, msg = self.exporter.export_bookings(bookings)

        self.assertEquals(len(self.api_client.created_bookings), 1)  # One new booking was added
        self.assertEquals(len(self.api_client.updated_bookings), 0)
        self.assertEquals(len(self.api_client.deleted_bookings), 0)
        self.assertEquals(self.api_client.created_bookings[0].price, 400.0)

        self.assertEquals(result['updated'], 0)
        self.assertEquals(result['created'], 1)
        self.assertEquals(result['deleted'], 0)

    def test_export_bookings_with_deletion(self):
        """
        Tests the export_bookings method with a booking deletion.
        """
        bookings = [
            Booking(date="2023-01-01", docnumber="12345", text="Test Booking",
                    debit_account="1100", credit_account="3001", price=100.0, vat_amount=20.0),
            Booking(date="2023-01-02", docnumber="12346", text="Another Booking",
                    debit_account="1100", credit_account="3001", price=200.0, vat_amount=40.0)
            # The third booking is intentionally omitted to simulate deletion
        ]

        result, msg = self.exporter.export_bookings(bookings)

        self.assertEquals(len(self.api_client.created_bookings), 0)
        self.assertEquals(len(self.api_client.updated_bookings), 0)
        self.assertEquals(len(self.api_client.deleted_bookings), 1)  # One booking was deleted
        self.assertEquals(self.api_client.deleted_bookings[0].docnumber, "12347")

        self.assertEquals(result['updated'], 0)
        self.assertEquals(result['created'], 0)
        self.assertEquals(result['deleted'], 1)

    def test_bookings_are_equal(self):
        """
        Tests the bookings_are_equal method of the BexioExporter.
        """
        booking1 = Booking(date="2023-01-01", docnumber="12345", text="Test Booking",
                           debit_account="1100", credit_account="3001", price=100.0, vat_amount=20.0)
        booking2 = Booking(date="2023-01-01", docnumber="12345", text="Test Booking",
                           debit_account="1100", credit_account="3001", price=100.0, vat_amount=20.0)

        self.assertTrue(self.exporter.bookings_are_equal(booking1, booking2))

    def test_bookings_are_not_equal(self):
        """
        Tests the bookings_are_equal method with different bookings.
        """
        booking1 = Booking(date="2023-01-01", docnumber="12345", text="Test Booking",
                           debit_account="1100", credit_account="3001", price=100.0, vat_amount=20.0)
        booking2 = Booking(date="2023-01-02", docnumber="12345", text="Test Booking",
                           debit_account="1100", credit_account="3001", price=110.0, vat_amount=20.0)

        self.assertFalse(self.exporter.bookings_are_equal(booking1, booking2))


class TestApiClient:
    """
    Mock API client for testing purposes.
    """

    def __init__(self, existing_bookings=None):
        """
        Initializes the TestApiClient with optional existing bookings.

        :param existing_bookings: A list of mock existing bookings.
        """
        self.existing_bookings = existing_bookings or []
        self.created_bookings = []
        self.updated_bookings = []
        self.deleted_bookings = []

    def get_existing_bookings(self, from_date, till_date):
        """
        Mock method to get existing bookings from Bexio.
        """
        return self.existing_bookings

    def create_booking(self, booking):
        """
        Mock method to create a booking in Bexio.
        """
        self.created_bookings.append(booking)
        return booking

    def update_booking(self, existing_booking, new_booking):
        """
        Mock method to update an existing booking in Bexio.
        """
        self.updated_bookings.append((existing_booking, new_booking))
        return new_booking

    def delete_booking(self, booking):
        """
        Mock method to delete a booking in Bexio.
        """
        self.deleted_bookings.append(booking)
