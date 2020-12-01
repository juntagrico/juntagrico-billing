from datetime import date, timedelta

from django import forms
from django.contrib.auth.decorators import permission_required, login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import get_template
from django.urls import reverse
from django.views.decorators.http import require_POST
from juntagrico.util import return_to_previous_location
from juntagrico.util.temporal import start_of_business_year, start_of_next_business_year
from juntagrico.util.xls import generate_excel
from juntagrico.views import get_menu_dict

from juntagrico_billing.dao.billdao import BillDao
from juntagrico_billing.entity.bill import BusinessYear, Bill
from juntagrico_billing.entity.settings import Settings
from juntagrico_billing.mailer import send_bill_notification
from juntagrico_billing.util.billing import get_billable_items, group_billables_by_member, create_bills_for_items, \
    get_open_bills
from juntagrico_billing.util.bookings import get_bill_bookings, get_payment_bookings


@permission_required('juntagrico.is_book_keeper')
def bills(request):
    """
    List of bills per year
    """
    renderdict = get_menu_dict(request)

    # get all business years
    business_years = list(BusinessYear.objects.all().order_by('start_date'))

    # if no year set, choose most recent year
    selected_year = None
    selected_year_name = request.session.get('bills_businessyear', None)
    if selected_year_name:
        selected_year = [year for year in business_years if year.name == selected_year_name][0]
    else:
        if len(business_years):
            selected_year = business_years[-1]
            request.session['bills_businessyear'] = selected_year.name

    bills_list = []
    pending_bills = 0
    percent_paid = 100

    # determine view state (all, open, open75, open50, open25, generate)
    states = ('all', 'open', 'open75', 'open50', 'open25', 'generate')
    state = request.GET.get('state', 'all')

    # array to set active tab state in template
    state_active = [(state == st and 'active') or '' for st in states]

    if selected_year:
        bills_list = selected_year.bills.all()
        if state == "generate":
            billable_items = get_billable_items(selected_year)
            pending_bills = len(group_billables_by_member(billable_items))

        elif state.startswith("open"):
            percent_str = state[4:]
            if percent_str:
                percent_paid = int(percent_str)
            bills_list = get_open_bills(selected_year, percent_paid)

    else:
        message = get_template('messages/no_businessyear.html').render()
        renderdict['messages'].append(message)

    renderdict.update({
        'business_years': business_years,
        'selected_year': selected_year,
        'bills_list': bills_list,
        'bills_count': len(bills_list),
        'pending_bills': pending_bills,
        'percent_paid': percent_paid,
        'email_form_disabled': True,
        'change_date_disabled': True,
        'state': state,
        'state_active': state_active
    })

    return render(request, "jb/bills.html", renderdict)


@permission_required('juntagrico.is_book_keeper')
@require_POST
def bills_setyear(request):
    # determine chosen billing year
    year = request.POST.get('year')
    request.session['bills_businessyear'] = year
    return return_to_previous_location(request)


@permission_required('juntagrico.is_book_keeper')
def bills_generate(request):
    # generate bills for current business year
    year_name = request.session['bills_businessyear']
    year = BusinessYear.objects.filter(name=year_name).first()

    billable_items = get_billable_items(year)

    create_bills_for_items(billable_items, year, date.today())

    return redirect(reverse('jb:bills-list'))


class DateRangeForm(forms.Form):
    fromdate = forms.DateField(
        widget=forms.DateInput(
            attrs={'class': 'col-md-2 form-control',
                   'id': 'id_fromdate'}))
    tilldate = forms.DateField(
        widget=forms.DateInput(
            attrs={'class': 'col-md-2 form-control',
                   'id': 'id_tilldate'}))


@permission_required('juntagrico.is_book_keeper')
def bookings_export(request):

    default_range = {
        'fromdate': start_of_business_year(),
        'tilldate': start_of_next_business_year() - timedelta(1)
    }

    renderdict = get_menu_dict(request)

    # daterange for bookings export
    if 'fromdate' in request.GET and 'tilldate' in request.GET:
        # request with query parameter
        daterange_form = DateRangeForm(request.GET)
    else:
        daterange_form = DateRangeForm(default_range)

    if daterange_form.is_valid():
        fromdate = daterange_form.cleaned_data['fromdate']
        tilldate = daterange_form.cleaned_data['tilldate']
        bill_bookings = get_bill_bookings(fromdate, tilldate)
        payment_bookings = get_payment_bookings(fromdate, tilldate)
    else:
        bill_bookings = []
        payment_bookings = []

    # export button pressed and date fields OK -> do excel export
    if ('export' in request.GET) and daterange_form.is_valid():
        # sort bookings on date and docnumber
        bookings = sorted(bill_bookings + payment_bookings,
                          key=lambda bk: (bk.date, bk.docnumber))
        return export_bookings(bookings, "bookings")

    # otherwise return page
    renderdict.update({
        'daterange_form': daterange_form,
        'bill_bookings_count': len(bill_bookings),
        'payment_bookings_count': len(payment_bookings),
    })

    return render(request, 'jb/bookings_export.html', renderdict)


def export_bookings(bookings, filename):
    fields = {
        'date': 'Datum',
        'docnumber': 'Belegnummer',
        'text': 'Text',
        'debit_account': 'Soll',
        'credit_account': 'Haben',
        'price': 'Betrag',
        'member_account': 'KS1 (Mitglied)'
    }

    return generate_excel(fields.items(), bookings, filename)


@login_required
def user_bills(request):
    member = request.user.member
    settings = Settings.objects.first()
    renderdict = get_menu_dict(request)
    renderdict.update({
        'bills': BillDao.bills_for_member(member),
        'paymenttype': settings.default_paymenttype,
        'menu': {'bills': 'active'},
    })
    return render(request, "jb/user_bills.html", renderdict)


@login_required
def user_bill(request, bill_id):
    member = request.user.member
    bill = get_object_or_404(Bill, id=bill_id)

    # only allow for bookkepper or the bills member
    if not (request.user.has_perms(('juntagrico.is_book_keeper',))
            or bill.member == member):
        raise PermissionDenied()

    settings = Settings.objects.first()

    renderdict = get_menu_dict(request)
    renderdict.update({
        'member': bill.member,
        'bill': bill,
        'today': date.today(),
        'payments': bill.payments.all(),
        'open_amount': bill.amount - bill.amount_paid,
        'paymenttype': settings.default_paymenttype,
    })
    return render(request, "jb/user_bill.html", renderdict)


@permission_required('juntagrico.is_book_keeper')
def bills_notify(request):
    """
    List of bills to send notification e-mails
    """
    renderdict = get_menu_dict(request)

    bills_list = list(Bill.objects.filter(notification_sent=False))

    if request.method == 'POST':
        for bill in bills_list:
            send_bill_notification(bill)
            bill.notification_sent = True
            bill.save()

        return return_to_previous_location(request)

    renderdict.update({
        'bills_list': bills_list,
        'bills_count': len(bills_list),
        'email_form_disabled': True,
        'change_date_disabled': True,
    })

    return render(request, "jb/bills_notify.html", renderdict)
