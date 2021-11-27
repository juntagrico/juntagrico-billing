from django.urls import path

from juntagrico_billing import views, views_payment

app_name = 'jb'
urlpatterns = [
    # bills (admin)
    path('jb/open_bills', views.open_bills, name='open-bills-list'),
    path('jb/pending_bills', views.pending_bills, name='pending-bills-list'),
    path('jb/unpublished_bills', views.unpublished_bills, name='unpublished-bills-list'),
    path('jb/bills_publish', views.bills_publish, name='bills-publish'),
    path('jb/bills_setyear', views.bills_setyear, name='bills-setyear'),
    path('jb/bills_generate', views.bills_generate, name='bills-generate'),
    path('jb/bills_notify', views.bills_notify, name='bills-notify'),
    path('jb/bill_recalc/<int:bill_id>', views.bill_recalc, name='bill-recalc'),

    # bookings export
    path('jb/bookings_export', views.bookings_export, name='bookings-export'),

    # bills (user)
    path('jb/user_bills', views.user_bills, name='user-bills'),
    path('jb/user_bill/<int:bill_id>', views.user_bill, name='user-bill'),
    path('jb/user_bill_pdf/<int:bill_id>', views.user_bill_pdf, name='user-bill-pdf'),

    # payments
    path('jb/payments_upload', views_payment.payments_upload, name='payments-upload')
]
