"""
test URL Configuration for juntagrico_billing development
"""
from django.urls import include, re_path
from django.contrib import admin
import juntagrico

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^impersonate/', include('impersonate.urls')),
    re_path(r'^', include('juntagrico.urls')),
    re_path(r'^', include('juntagrico_billing.urls')),
    re_path(r'^$', juntagrico.views.home),
]
