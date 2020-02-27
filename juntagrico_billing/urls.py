from django.conf.urls import url
from juntagrico_billing import views
from juntagrico_billing import views_legacy

urlpatterns = [
    url(r'^jb/bills$', views.bills),
    url(r'^jb/bills_setyear', views.bills_setyear, name="bills-setyear"),
    url(r'^jb/bills_generate', views.bills_generate, name="bills-generate"),

    # legacy
    url(r'^jb/subscription_bookings$', views_legacy.subscription_bookings)
]

