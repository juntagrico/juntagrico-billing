from django.conf.urls import url
from juntagrico_billing import views_legacy

urlpatterns = [


    # legacy
    url(r'^jb/subscription_bookings$', views_legacy.subscription_bookings)
]
