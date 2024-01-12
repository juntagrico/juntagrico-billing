"""
test URL Configuration for juntagrico_billing development
"""
from django.urls import include, path
from django.contrib import admin
import juntagrico

urlpatterns = [
    path('admin/', admin.site.urls),
    path('impersonate/', include('impersonate.urls')),
    path('', include('juntagrico.urls')),
    path('', include('juntagrico_billing.urls')),
    path('', juntagrico.views.home),
]
