from django.urls import path

from . import views

app_name = "locations"

urlpatterns = [
    path("sell-land-in-agra/", views.area_index, name="area_index"),
    path("sell-land-in-agra/<slug:slug>/", views.locality_detail, name="locality"),
    path("sell-plot-agra/", views.type_landing, {"kind": "plot"}, name="sell_plot"),
    path("sell-agricultural-land-agra/", views.type_landing, {"kind": "agricultural"}, name="sell_agricultural"),
    path("sell-commercial-land-agra/", views.type_landing, {"kind": "commercial"}, name="sell_commercial"),
    path("price-estimator/", views.estimator, name="estimator"),
    path("price-estimator/api/", views.estimator_api, name="estimator_api"),
]
