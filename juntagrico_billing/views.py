from datetime import date, timedelta

from django import forms
from django.contrib.auth.decorators import permission_required, login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import get_template
from django.urls import reverse
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from juntagrico.util import return_to_previous_location
from juntagrico.util.temporal import start_of_business_year, \
    start_of_next_business_year
from juntagrico.util.xls import generate_excel
from juntagrico_billing.dao.billdao import BillDao
from juntagrico_billing.entity.bill import BusinessYear, Bill
from juntagrico_billing.entity.settings import Settings
from juntagrico_billing.mailer import send_bill_notification
from juntagrico_billing.util.billing import get_billable_subscription_parts, \
    group_billables_by_member, create_bills_for_items, get_open_bills, \
    scale_subscriptionpart_price, recalc_bill, get_unpublished_bills, \
    publish_bills
from juntagrico_billing.util.qrbill import is_qr_iban, get_qrbill_svg
from juntagrico_billing.util.pdfbill import PdfBillRenderer
from juntagrico_billing.util.bookings import get_bill_bookings, \
    get_payment_bookings
from django.utils.translation import gettext as _


@permission_required('juntagrico.is_book_keeper')
def open_bills(request):
    """
    List of open bills per year
    """
    business_years, selected_year = get_years_and_selected(request)

    bills_list = []
    percent_paid = 100

    # determine view state (all, open, open75, open50, open25)
    states = ('open', 'open75', 'open50', 'open25')
    state = request.GET.get('state', 'open')

    # array to set active tab state in template
    state_active = [(state == st and 'active') or '' for st in states]

    if selected_year:
        percent_str = state[4:]
        if percent_str:
            percent_paid = int(percent_str)
        bills_list = get_open_bills(selected_year, percent_paid)

    renderdict = {
        'business_years': business_years,
        'selected_year': selected_year,
        'bills_list': bills_list,
        'percent_paid': percent_paid,
        'email_form_disabled': True,
        'change_date_disabled': True,
        'state': state,
        'state_active': state_active
    }

    return render(request, "jb/open_bills.html", renderdict)


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

    billable_items = get_billable_subscription_parts(year)

    create_bills_for_items(billable_items, year, date.today())

    return redirect(reverse('jb:unpublished-bills-list'))


@permission_required('juntagrico.is_book_keeper')
def pending_bills(request):
    """
    List pending bills (bills to generate)
    """
    business_years, selected_year = get_years_and_selected(request)
    if selected_year:
        billable_items = get_billable_subscription_parts(selected_year)
        members_and_parts = group_billables_by_member(billable_items).items()
        pending_bills = [
            (
                member,
                get_subscription(parts),
                get_short_parts(parts),
                get_price(parts, selected_year),
                get_existing_bills(member, selected_year)
            )
            for member, parts in members_and_parts
        ]

    renderdict = {
        'business_years': business_years,
        'selected_year': selected_year,
        'pending_bills': pending_bills,
        'email_form_disabled': True,
        'change_date_disabled': True,
    }

    return render(request, "jb/pending_bills.html", renderdict)


# helper functions for pending_bills
def get_subscription(parts):
    if len(parts) == 0:
        return None

    return parts[0].subscription


def get_short_parts(parts):

    def short_name(part):
        if part.type.size.product.is_extra:
            return _('Extrasubscription')
        else:
            return _('Subscription')

    return ", ".join([short_name(part) for part in parts])


def get_price(parts, year):
    prices = [
        scale_subscriptionpart_price(
            part,
            year.start_date,
            year.end_date)
        for part in parts
    ]
    return sum(prices)


def get_existing_bills(member, year):
    bills = member.bills.filter(business_year=year)
    return bills


@permission_required('juntagrico.is_book_keeper')
def unpublished_bills(request):
    """
    Show bills that are not published (not yet
    visible to members)
    """
    bills_list = get_unpublished_bills()

    renderdict = {
        'bills_list': bills_list,
        'search_disabled': True,
        'email_form_disabled': True,
        'change_date_disabled': True,
    }

    return render(request, "jb/unpublished_bills.html", renderdict)


@permission_required('juntagrico.is_book_keeper')
def bills_publish(request):
    """
    POST handler for publishing bills.
    Called from unpublished_bills view.
    """
    if request.method == 'POST':
        selected_ids = request.POST.getlist('_selected')
        publish_bills(selected_ids)

    return redirect(reverse('jb:unpublished-bills-list'))


@permission_required('juntagrico.is_book_keeper')
def bill_recalc(request, bill_id):
    bill = Bill.objects.get(pk=bill_id)
    recalc_bill(bill)

    next_url = request.GET.get('next')
    return redirect(next_url)


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
        bill_bookings_sorted = sorted(
            bill_bookings, key=lambda bk: (bk.date, bk.docnumber))
        payment_bookings_sorted = sorted(
            payment_bookings, key=lambda bk: (bk.date, bk.docnumber))
        return export_bookings(
            bill_bookings_sorted + payment_bookings_sorted, "bookings")

    # otherwise return page
    renderdict = {
        'daterange_form': daterange_form,
        'bill_bookings_count': len(bill_bookings),
        'payment_bookings_count': len(payment_bookings),
    }

    return render(request, 'jb/bookings_export.html', renderdict)


def export_bookings(bookings, filename):
    fields = {
        'date': 'Datum',
        'docnumber': 'Belegnummer',
        'text': 'Text',
        'debit_account': 'Soll',
        'credit_account': 'Haben',
        'price': 'Betrag',
        'member_account': 'KS1 (Mitglied)',
        'vat_amount': "MWST"
    }

    return generate_excel(fields.items(), bookings, filename)


@login_required
def user_bills(request):
    member = request.user.member
    settings = Settings.objects.first()
    renderdict = {
        'bills': BillDao.bills_for_member(member),
        'paymenttype': settings.default_paymenttype,
        'menu': {'bills': 'active'},
    }
    return render(request, "jb/user_bills.html", renderdict)


@login_required
def user_bill(request, bill_id):
    member = request.user.member
    bill = get_object_or_404(Bill, id=bill_id)

    # only allow for bookkepper or the bills member
    if not (request.user.has_perms(('juntagrico.is_book_keeper',)) or bill.member == member):
        raise PermissionDenied()

    settings = Settings.objects.first()

    # add QR-Bill part if QR-IBAN
    if is_qr_iban(settings.default_paymenttype.iban):
        qr_svg = get_qrbill_svg(bill, settings.default_paymenttype)
    else:
        qr_svg = None

    renderdict = {
        'member': bill.member,
        'bill': bill,
        'today': date.today(),
        'payments': bill.payments.all(),
        'open_amount': bill.amount - bill.amount_paid,
        'paymenttype': settings.default_paymenttype,
        'vat_number': settings.vat_number,
        'vat_percent': bill.vat_rate * 100,
        'qr_svg': qr_svg
    }
    return render(request, "jb/user_bill.html", renderdict)


@login_required
def user_bill_pdf(request, bill_id):
    member = request.user.member
    bill = get_object_or_404(Bill, id=bill_id)

    # only allow for bookkeeper or the bills member
    if not (request.user.has_perms(('juntagrico.is_book_keeper',)) or bill.member == member):
        raise PermissionDenied()

    filename = "Rechnung %d.pdf" % bill.id
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = \
        "attachment; filename=\"" + filename + "\""

    PdfBillRenderer().render(bill, response)
    return response


@permission_required('juntagrico.is_book_keeper')
def bills_notify(request):
    """
    List of bills to send notification e-mails
    """
    bills_list = list(Bill.objects.filter(notification_sent=False))

    if request.method == 'POST':
        for bill in bills_list:
            send_bill_notification(bill)
            bill.notification_sent = True
            bill.save()

        return return_to_previous_location(request)

    renderdict = {
        'bills_list': bills_list,
        'bills_count': len(bills_list),
        'email_form_disabled': True,
        'change_date_disabled': True,
    }

    return render(request, "jb/bills_notify.html", renderdict)


def get_years_and_selected(request):
    """
    get selected year from request.
    If none is selected, select the most
    recent year.
    """
    # get all business years
    business_years = list(BusinessYear.objects.all().order_by('start_date'))

    if len(business_years) == 0:
        # add message 'no businessyear'
        messages = getattr(request, 'member_messages', []) or []
        messages.extend(get_template('messages/no_businessyear.html').render())
        request.member_messages = messages

    # if no year set, choose most recent year
    selected_year = None
    selected_year_name = request.session.get('bills_businessyear', None)
    if selected_year_name:
        selected_year = [
            year for year in business_years
            if year.name == selected_year_name][0]
    else:
        if len(business_years):
            selected_year = business_years[-1]
            request.session['bills_businessyear'] = selected_year.name

    return (business_years, selected_year)
