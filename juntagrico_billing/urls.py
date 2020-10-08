from django.urls import path
from juntagrico_billing import views
from juntagrico_billing import views_legacy

app_name = 'jb'
urlpatterns = [
    # bills (admin)
    path('jb/bills', views.bills, name='bills-list'),
    path('jb/bills_setyear', views.bills_setyear, name='bills-setyear'),
    path('jb/bills_generate', views.bills_generate, name='bills-generate'),

    # bookings export
    path('jb/bookings_export', views.bookings_export, name='bookings-export'),
    path('jb/bill_bookings', views.bill_bookings, name='bill-bookings'),
    path('jb/payment_bookings', views.payment_bookings, name='payment-bookings'),

    # bills (user)
    path('jb/bills/user', views.bills_user, name='user-bills'),

    # legacy
    path('jb/subscription_bookings', views_legacy.subscription_bookings)
]
