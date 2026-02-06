import re
from requests import Session
from datetime import date

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
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
            })

        self.accounts_by_id = {}
        self.account_ids_by_number = {}
        self.currency_ids = {}

    def load_base_data(self):
        """
        Loads accounts from Bexio in a dictionary
        """
        if len(self.accounts_by_id):
            return

        # Fetch accounts from Bexio
        response = self.session.get("https://api.bexio.com/2.0/accounts")
        response.raise_for_status()

        for account in response.json():
            self.accounts_by_id[account['id']] = account['account_no']
            self.account_ids_by_number[account['account_no']] = account['id']

        # fetch currency IDs
        response = self.session.get("https://api.bexio.com/3.0/currencies")
        response.raise_for_status()

        for currency in response.json():
            self.currency_ids[currency['name']] = currency['id']

    def booking_to_dict(self, booking):
        return {
            "type": "manual_single_entry",
            "date": booking.date.isoformat(),
            "entries": [
                {
                    "description": f"{booking.text} jb:{booking.docnumber}",  # add juntagrico billing docnumber to text
                    "debit_account_id": self.get_account_id(booking.debit_account),
                    "credit_account_id": self.get_account_id(booking.credit_account),
                    "amount": booking.price,
                    "tax_amount": booking.vat_amount,
                    "currency_id": self.get_currency_id("CHF"),
                }
            ]
        }

    def get_account_id(self, account_nr):
        try:
            return self.account_ids_by_number[account_nr]
        except KeyError:
            raise Exception(f"Unknown account number {account_nr}") from None

    def get_account_nummber(self, account_id):
        if not account_id:
            raise Exception("entry has empty account_id")
        return self.accounts_by_id[account_id]

    def get_currency_id(self, currency_name):
        try:
            return self.currency_ids[currency_name]
        except KeyError:
            raise Exception(f"Unknown currency {currency_name}") from None

    def get_existing_bookings(self, from_date, till_date):
        """
        Fetches existing bookings from Bexio within the specified date range.
        Uses pagination to fetch all bookings if there are more than 2000 entries.

        :param from_date: The start date for the bookings to fetch.
        :param till_date: The end date for the bookings to fetch.
        :param account: acount for filtering, must appear on either side of booking.
        :return: A list of existing bookings.
        """
        self.load_base_data()

        # Fetch all manual entries using pagination
        limit = 2000
        offset = 0
        all_envelopes = []

        while True:
            response = self.session.get(
                "https://api.bexio.com/3.0/accounting/manual_entries",
                params={"limit": limit, "offset": offset}
            )
            response.raise_for_status()

            envelopes = response.json()
            all_envelopes.extend(envelopes)

            # If we received fewer entries than the limit, we've fetched all entries
            if len(envelopes) < limit:
                break

            offset += limit

        # prepare regex for docnumber matching
        docnum_regex = re.compile(r'(.+) jb:(\d+)$')

        result = []
        for envelope in all_envelopes:
            entries = envelope.get('entries', [])

            # only consider first entry in envelope
            entry = entries[0]

            # filter by date range
            entry_date = date.fromisoformat(entry['date'])
            if not (from_date <= entry_date <= till_date):
                continue

            # parse docnumber from entry description
            m = docnum_regex.match(entry['description'])

            # only consider entries where the description ends with jb:<docnumber>
            if not m:
                continue

            text = m.group(1)
            docnum = m.group(2)
            debit_account = self.accounts_by_id.get(entry['debit_account_id'])
            credit_account = self.accounts_by_id.get(entry['credit_account_id'])

            booking = Booking(
                entry_date,
                docnum,
                text,
                debit_account,
                credit_account,
                entry['amount'],
                entry.get('tax_amount', 0.0)
            )
            booking.id = envelope.get('id')
            result.append(booking)

        return result

    def create_booking(self, booking):
        """
        Creates a new booking in Bexio.

        :param booking: The booking to create.
        """
        self.load_base_data()

        entry_data = self.booking_to_dict(booking)

        response = self.session.post("https://api.bexio.com/3.0/accounting/manual_entries", json=entry_data)
        if not response.ok:
            raise Exception(f"Failed to create booking: {response.json()}")

        print(f"create_booking response: {response.json()}")

    def update_booking(self, existing_booking, new_booking):
        """
        Updates an existing booking in Bexio.

        :param existing_booking: The existing booking to update.
        :param new_booking: The new booking data.
        """
        self.load_base_data()

        entry_data = self.booking_to_dict(new_booking)
        response = self.session.put(f"https://api.bexio.com/3.0/accounting/manual_entries/{existing_booking.id}", json=entry_data)
        response.raise_for_status()

    def delete_booking(self, booking):
        """
        Deletes a booking from Bexio.

        :param booking: The booking to delete.
        """
        response = self.session.delete(f"https://api.bexio.com/3.0/accounting/manual_entries/{booking.id}")
        response.raise_for_status()


class Booking(object):
    """
    local definition of Booking class
    to avoid importing from django.
    """
    def __init__(self, date=None, docnumber=None, text=None, debit_account=None,
                 credit_account=None, price=0.0, vat_amount=0.0, id=None):
        self.date = date
        self.docnumber = docnumber
        self.text = text
        self.debit_account = debit_account
        self.credit_account = credit_account
        self.price = price
        self.vat_amount = vat_amount
        self.id = id

# some test code to fetch existing bookings
#
# if __name__ == "__main__":
#     from datetime import date

#     api_key = "API_KEY"  # replace with your actual API key
#     client = BexioApiClient(api_key)

#     bookings = client.get_existing_bookings(date(2025, 1, 1), date(2025, 12, 31))

#     # write the booking to a file for debugging purposes
#     for booking in bookings:
#         with open("bookings_debug.txt", "a") as f:             
#             f.write(f"{booking.date} {booking.docnumber} {booking.text} {booking.debit_account} {booking.credit_account} {booking.price} {booking.vat_amount}\n")
