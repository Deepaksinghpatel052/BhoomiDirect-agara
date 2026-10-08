from django.urls import path

from . import views

app_name = "partners"

urlpatterns = [
    path("channel-partners/", views.join, name="join"),
    path("partner/", views.portal, name="portal"),
    path("partner/refer-owner/", views.refer_owner, name="refer_owner"),
    path("partner/refer-buyer/", views.refer_buyer, name="refer_buyer"),
]
