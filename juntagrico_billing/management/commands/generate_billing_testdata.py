import datetime

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from juntagrico_billing.models.bill import BusinessYear


class Command(BaseCommand):
    help = "Generate billing test data for development environments. DO NOT USE IN PRODUCTION."

    # entry point used by manage.py
    def handle(self, *args, **options):
        settings.TMP_DISABLE_EMAILS = True  # prevent sending emails while creating testdata
        try:
            call_command('loaddata', 'billing.json')
            this_year = datetime.date.today().year
            start_of_this_year = datetime.date(this_year, 1, 1)
            end_of_this_year = datetime.date(this_year, 12, 31)
            BusinessYear.objects.create(
                name=str(this_year), start_date=start_of_this_year, end_date=end_of_this_year
            )
        finally:
            del settings.TMP_DISABLE_EMAILS
