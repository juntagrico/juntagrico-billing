from datetime import date

from django.contrib.auth.decorators import permission_required, login_required
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from juntagrico_billing.config import Config as BConfig
from juntagrico.util import return_to_previous_location
from juntagrico.views import get_menu_dict

from juntagrico_billing.dao.billdao import BillDao
from juntagrico_billing.entity.bill import BusinessYear, Bill
from juntagrico_billing.util.billing import get_billable_subscriptions, create_subscription_bill


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
    if not selected_year:
        if len(business_years):
            selected_year = business_years.last()
            request.session['billing_businessyear'] = selected_year

    if selected_year:
        bills_list = selected_year.bills.all()
    else:
        bills_list = []

    renderdict.update({
        'business_years' : business_years,
        'selected_year' : selected_year,
        'bills_list' : bills_list,
        'billable_subscriptions' : get_billable_subscriptions(selected_year),
        'email_form_disabled' : True
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
        create_subscription_bill(subs, year, date.today())

    return return_to_previous_location(request)


@permission_required('juntagrico.is_book_keeper')
def bills_delete(request, id):
    # delete a bill
    bill = get_object_or_404(Bill, pk=id)
    bill.delete()

    return return_to_previous_location(request)


@login_required
def bills(request):
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


