from django.conf.urls import url
from juntagrico_billing import views

urlpatterns = [
    url(r'^jb/subscription_bookings$', views.subscription_bookings)
]
