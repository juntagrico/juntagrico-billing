from datetime import date, timedelta

from django import forms
from django.contrib.auth.decorators import permission_required
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect
from django.shortcuts import render
from juntagrico.util import return_to_previous_location
from juntagrico.views import get_menu_dict
from juntagrico_billing.entity.billing import BusinessYear, Bill
from juntagrico_billing.util.bills import get_billable_subscriptions


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
    
    renderdict['business_years'] = business_years
    renderdict['selected_year'] = selected_year

    if selected_year:
        bills_list = selected_year.bills.all()
    else:
        bills_list = [] 
    renderdict['bills_list'] = bills_list

    renderdict['billable_subscriptions'] = get_billable_subscriptions(selected_year)

    return render(request, "jb/bills.html", renderdict)

@permission_required('juntagrico.is_book_keeper')
@require_POST
def bills_setyear(request):
    # determine chosen billing year
    request.session['billing_year'] = year
    return return_to_previous_location(request)



@permission_required('juntagrico.is_book_keeper')
def bills_generate(request):
    pass
