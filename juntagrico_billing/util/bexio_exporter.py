
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
        try:
            existing_bookings = self.api_client.get_existing_bookings(self.from_date, self.till_date)

            return (self.sync_bookings(existing_bookings, bookings), "OK")
        except Exception as e:
            return ({}, str(e))

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
                    # bexio only accepts bookings with different debit and credit accounts
                    # so we need to update or delete the existing booking accordingly
                    if booking.debit_account != booking.credit_account:
                        self.api_client.update_booking(existing_booking, booking)
                        result['updated'] += 1
                    else:
                        self.api_client.delete_booking(existing_booking)
                        result['deleted'] += 1

            else:
                if booking.debit_account == booking.credit_account:
                    # bexio does not allow bookings with the same debit and credit account
                    continue
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
        VAT amount is not considered for comparison.

        :param booking1: The first booking to compare.
        :param booking2: The second booking to compare.
        :return: True if bookings are equal, False otherwise.
        """
        return (booking1.docnumber == booking2.docnumber and
                booking1.price == booking2.price and
                booking1.date == booking2.date and
                booking1.debit_account == booking2.debit_account and
                booking1.credit_account == booking2.credit_account and
                booking1.text == booking2.text)
