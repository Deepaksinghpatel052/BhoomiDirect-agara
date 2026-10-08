from django.urls import path

from . import views

app_name = "listings"

urlpatterns = [
    path("buy-property-in-agra/", views.listing_list, name="list"),
    path("buy-property-in-agra/<slug:slug>/", views.listing_detail, name="detail"),
    path("buy-property-in-agra/<slug:slug>/inquiry/", views.listing_inquiry, name="inquiry"),
]
