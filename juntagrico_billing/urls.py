from django.urls import path
from juntagrico_billing import views
from juntagrico_billing import views_legacy

urlpatterns = [
    path('jb/bills', views.bills),
    path('jb/bills_setyear', views.bills_setyear, name="bills-setyear"),
    path('jb/bills_generate', views.bills_generate, name="bills-generate"),
    path('jb/bills_delete/<int:id>', views.bills_delete, name="bills-delete"),

    # legacy
    path('jb/subscription_bookings', views_legacy.subscription_bookings)
]

