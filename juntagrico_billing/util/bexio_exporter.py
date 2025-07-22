from requests import Session
from juntagrico_billing.util.bookings import Booking


class BexioExporter:
    """
    A class to handle exporting bookings to Bexio (https://www.bexio.com).
    """

    def __init__(self, api_client, from_date=None, till_date=None):
        """
        Initializes the BexioExporter with an API client.

        :param api_client: An instance of the API client to interact with Bexio.
        """
        self.api_client = api_client
        self.from_date = from_date
        self.till_date = till_date

    def export_bookings(self, bookings):
        """
        Exports the list of bookings to Bexio.

        First, load all the manual entries from bexio into memory.
        Then, sync with the passed bookings and export or delete bexio entries as necessary.

        This allows for exporting the bookings repeatedly without duplicating entries.

        :param bookings: The list of bookings to be exported.
        :return: Response from the Bexio API.
        """
        existing_bookings = self.api_client.get_existing_bookings(self.from_date, self.till_date)

        return self.sync_bookings(existing_bookings, bookings)

    def sync_bookings(self, existing_bookings, new_bookings):
        """
        Syncs existing bookings with new bookings.

        :param existing_bookings: The bookings already present in Bexio.
        :param new_bookings: The new bookings to be exported.
        :return: Response from the Bexio API after syncing.
        """
        existing_by_docnumber = {booking.docnumber: booking for booking in existing_bookings}
        new_by_docnumber = {booking.docnumber: booking for booking in new_bookings}

        result = {
            'created': 0,
            'updated': 0,
            'deleted': 0
        }
        
        for booking in new_bookings:
            if booking.docnumber in existing_by_docnumber:
                existing_booking = existing_by_docnumber[booking.docnumber]
                # Check if the existing booking is equal to the new booking
                if not self.bookings_are_equal(existing_booking, booking):
                    self.api_client.update_booking(existing_booking, booking)
                    result['updated'] += 1
            else:
                self.api_client.create_booking(booking)
                result['created'] += 1

        for booking in existing_bookings:
            if booking.docnumber not in new_by_docnumber:
                self.api_client.delete_booking(booking)
                result['deleted'] += 1

        return result

    def bookings_are_equal(self, booking1, booking2):
        """
        Compares two bookings to determine if they are equal.

        :param booking1: The first booking to compare.
        :param booking2: The second booking to compare.
        :return: True if bookings are equal, False otherwise.
        """
        return (booking1.docnumber == booking2.docnumber and
                booking1.price == booking2.price and
                booking1.vat_amount == booking2.vat_amount and
                booking1.date == booking2.date and
                booking1.debit_account == booking2.debit_account and
                booking1.credit_account == booking2.credit_account and
                booking1.text == booking2.text)


class BexioApiClient:
    """
    A client to interact with the Bexio API.
    """

    def __init__(self, api_key):
        """
        Initializes the BexioApiClient with an API key.

        :param api_key: The API key to authenticate with Bexio.
        """
        self.api_key = api_key
        self.session = Session()
        self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def get_existing_bookings(self, from_date, till_date):
        """
        Fetches existing bookings from Bexio within the specified date range.

        :param from_date: The start date for the bookings to fetch.
        :param till_date: The end date for the bookings to fetch.
        :return: A list of existing bookings.
        """
        response = self.session.get(f"https://api.bexio.com/2.0/bookings?from={from_date}&to={till_date}")
        response.raise_for_status()
        return [Booking(**data) for data in response.json()]

    def create_booking(self, booking):
        """
        Creates a new booking in Bexio.

        :param booking: The booking to create.
        """
        response = self.session.post("https://api.bexio.com/2.0/bookings", json=booking.to_dict())
        response.raise_for_status()

    def update_booking(self, existing_booking, new_booking):
        """
        Updates an existing booking in Bexio.

        :param existing_booking: The existing booking to update.
        :param new_booking: The new booking data.
        """
        response = self.session.put(f"https://api.bexio.com/2.0/bookings/{existing_booking.id}", json=new_booking.to_dict())
        response.raise_for_status()

    def delete_booking(self, booking):
        """
        Deletes a booking from Bexio.

        :param booking: The booking to delete.
        """
        response = self.session.delete(f"https://api.bexio.com/2.0/bookings/{booking.id}")
        response.raise_for_status()
