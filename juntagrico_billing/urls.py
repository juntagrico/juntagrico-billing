from django.urls import path

from juntagrico_billing import views

app_name = 'jb'
urlpatterns = [
    # bills (admin)
    path('jb/bills', views.bills, name='bills-list'),
    path('jb/bills_setyear', views.bills_setyear, name='bills-setyear'),
    path('jb/bills_generate', views.bills_generate, name='bills-generate'),
    path('jb/bills_notify', views.bills_notify, name='bills-notify'),

    # bookings export
    path('jb/bookings_export', views.bookings_export, name='bookings-export'),

    # bills (user)
    path('jb/user_bills', views.user_bills, name='user-bills'),
    path('jb/user_bill/<int:bill_id>', views.user_bill, name='user-bill'),
]
