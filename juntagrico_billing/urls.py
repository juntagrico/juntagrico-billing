from django.urls import path
from juntagrico_billing import views
from juntagrico_billing import views_legacy

app_name = 'billing'
urlpatterns = [
    path('', views.bills, name='list'),
    path('setyear', views.bills_setyear, name='setyear'),
    path('generate', views.bills_generate, name='generate'),
    path('<int:id>/delete', views.bills_delete, name='delete'),
    path('user', views.bills_user, name='list-user'),
    # path('<int:id>', views.detail, name='detail'),
    # path('user/<int:id>', views.detail_user, name='detail-user'),
    # path('<int:id>/qrcode', views.qrcode, name='qrcode'),

    # legacy
    path('subscription_bookings', views_legacy.subscription_bookings, name='subscription-bookings')
]

