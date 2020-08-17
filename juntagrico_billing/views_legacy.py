import datetime

from django import forms
from django.contrib.auth.decorators import permission_required
from django.shortcuts import render
from juntagrico.util.temporal import start_of_business_year, start_of_next_business_year
from juntagrico.util.xls import generate_excel
from juntagrico.views import get_menu_dict

from juntagrico_billing.util.bookings import subscription_bookings_by_date, extrasub_bookings_by_date


@permission_required('juntagrico.is_book_keeper')
def subscription_bookings(request):
    """
    List of subscriptions
    """

    class DateRangeForm(forms.Form):
        fromdate = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control'}))
        tilldate = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control'}))

    default_range = {
        'fromdate': start_of_business_year(),
        'tilldate': start_of_next_business_year() - datetime.timedelta(1)
    }

    if 'fromdate' in request.GET and 'tilldate' in request.GET:
        # request with query parameter
        daterange_form = DateRangeForm(request.GET)
    else:
        daterange_form = DateRangeForm(default_range)

    if daterange_form.is_valid():
        fromdate = daterange_form.cleaned_data['fromdate']
        tilldate = daterange_form.cleaned_data['tilldate']
        # list of bookings for subscriptions and extra subscriptions
        bookings = subscription_bookings_by_date(fromdate, tilldate)
        bookings.extend(extrasub_bookings_by_date(fromdate, tilldate))
        # sort by date and member
        bookings.sort(key=lambda b: b.docnumber)
    else:
        bookings = []

    if request.GET.get('format', '') == "xlsx":
        return export_bookings(bookings)
    else:
        renderdict = get_menu_dict(request)
        renderdict.update({
            'daterange_form': daterange_form,
            'bookings': bookings
        })
        return render(request, "jb/subscription_bookings.html",
                      renderdict)


def export_bookings(bookings):
    fields = {
        'date': 'Datum',
        'docnumber': 'Belegnummer',
        'text': 'Text',
        'debit_account': 'Soll',
        'credit_account': 'Haben',
        'price': 'Betrag',
        'member_account': 'KS1 (Mitglied)'
    }

    return generate_excel(fields.items(), bookings, "buchungen")
