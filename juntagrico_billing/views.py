from datetime import date, timedelta

from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.template.loader import get_template
from django import forms

from juntagrico.entity.extrasubs import ExtraSubscription
from juntagrico.entity.subs import Subscription
from juntagrico.util.temporal import start_of_business_year, start_of_next_business_year

from juntagrico_billing.config import Config as BConfig
from juntagrico.util import return_to_previous_location
from juntagrico.util.xls import generate_excel
from juntagrico.views import get_menu_dict

from juntagrico_billing.dao.billdao import BillDao
from juntagrico_billing.entity.bill import BusinessYear, Bill
from juntagrico_billing.util.billing import get_billable_subscriptions, create_subscription_bill, create_extra_sub_bill
from juntagrico_billing.util.bookings import get_bill_bookings, get_payment_bookings

@permission_required('juntagrico.is_book_keeper')
def bills(request):
    """
    List of bills per year
    """
    renderdict = get_menu_dict(request)

    # get all business years
    business_years = BusinessYear.objects.all().order_by('start_date')

    # if no year set, choose most recent year
    selected_year = request.session.get('billing_businessyear', None)
    if not selected_year and len(business_years):
        selected_year = business_years.last()
        request.session['billing_businessyear'] = selected_year

    if selected_year:
        bills_list = selected_year.bills.all()
        subscription_list = get_billable_subscriptions(selected_year)
    else:
        bills_list = []
        subscription_list = []
        message = get_template('messages/no_businessyear.html').render()
        renderdict['messages'].append(message)

    renderdict.update({
        'business_years': business_years,
        'selected_year': selected_year,
        'bills_list': bills_list,
        'billable_subscriptions': subscription_list,
        'email_form_disabled': True,
        'change_date_disabled': True
    })

    return render(request, "jb/bills.html", renderdict)


@permission_required('juntagrico.is_book_keeper')
@require_POST
def bills_setyear(request):
    # determine chosen billing year
    year = request.POST.get('year')
    request.session['billing_businessyear'] = year
    return return_to_previous_location(request)


@permission_required('juntagrico.is_book_keeper')
def bills_generate(request):
    # generate bills for current business year
    year = request.session['billing_businessyear']
    billable_subscriptions = get_billable_subscriptions(year)

    for subs in billable_subscriptions:
        if isinstance(subs, Subscription):
            create_subscription_bill(subs, year, date.today())
        if isinstance(subs, ExtraSubscription):
            create_extra_sub_bill(subs, year, date.today())

    return return_to_previous_location(request)


class DateRangeForm(forms.Form):
    fromdate = forms.DateField(
                widget=forms.DateInput(
                    attrs={'class': 'col-sm-2 form-control',
                            'id': 'id_fromdate'}))
    tilldate = forms.DateField(
                widget=forms.DateInput(
                    attrs={'class': 'col-sm-2 form-control',
                            'id': 'id_tilldate'}))


@permission_required('juntagrico.is_book_keeper')
def bookings_export(request):

    default_range = {
        'fromdate': start_of_business_year(),
        'tilldate': start_of_next_business_year() - timedelta(1)
    }

    renderdict = get_menu_dict(request)

    # get all business years
    business_years = BusinessYear.objects.all().order_by('start_date')

    # if no year set in request, get from session or choose most recent year
    businessyear = request.GET.get('businessyear', None)
    if not businessyear:
        businessyear = request.session.get('billing_businessyear', None)
        if not businessyear and len(business_years):
            businessyear = business_years.last()

    # daterange for payments export
    if 'fromdate' in request.GET and 'tilldate' in request.GET:
        # request with query parameter
        daterange_form = DateRangeForm(request.GET)
    else:
        daterange_form = DateRangeForm(default_range)

    renderdict.update({
        'business_years': business_years,
        'businessyear': businessyear,
        'daterange_form': daterange_form,
    })

    return render(request, 'jb/bookings_export.html', renderdict)

@permission_required('juntagrico.is_book_keeper')
def bill_bookings(request):
    year = request.GET['businessyear']
    businessyear = BillDao.businessyear_by_name(year)

    bookings = get_bill_bookings(businessyear)
    return export_bookings(bookings, "bills")


@permission_required('juntagrico.is_book_keeper')
def payment_bookings(request):
    daterange_form = DateRangeForm(request.GET)

    bookings = get_payment_bookings(daterange_form.fromdate, daterange_form.tilldate)
    return export_bookings(bookings, "payments")
    

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
def bills_user(request):
    member = request.user.member
    subs = list(member.old_subscriptions.all())
    subs.append(member.subscription)
    subs.append(member.future_subscription)
    renderdict = get_menu_dict(request)
    renderdict.update({
        'bills': BillDao.bills_for_billables(subs),
        'esr': BConfig.esr(),
        'menu': {'bills': 'active'},
    })
    return render(request, "jb/user_bills.html", renderdict)
