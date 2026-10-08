from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.overview, name="overview"),
    path("leads/", views.leads, name="leads"),
    path("leads/export/", views.leads_export, name="leads_export"),
    path("pipeline/", views.pipeline, name="pipeline"),
    path("pipeline/move/", views.pipeline_move, name="pipeline_move"),
    path("leads/<int:pk>/", views.lead_detail, name="lead_detail"),
    path("leads/<int:pk>/assign/", views.lead_assign, name="lead_assign"),
    path("leads/<int:pk>/status/", views.lead_status, name="lead_status"),
    path("leads/<int:pk>/note/", views.lead_note, name="lead_note"),
    path("leads/<int:pk>/visit/", views.visit_create, name="visit_create"),
    path("leads/<int:pk>/evaluation/", views.evaluation_save, name="evaluation_save"),
    path("leads/<int:pk>/legal/", views.legal_save, name="legal_save"),
    path("leads/<int:pk>/offer/", views.offer_create, name="offer_create"),
    path("leads/<int:pk>/acquire/", views.acquire, name="acquire"),
    path("offers/<int:offer_pk>/update/", views.offer_staff_update, name="offer_update"),
    path("site-visits/", views.site_visits, name="site_visits"),
    path("site-visits/<int:visit_pk>/report/", views.visit_report, name="visit_report"),
    path("acquired/", views.acquisitions_list, name="acquisitions"),
    path("acquired/<int:acquisition_pk>/publish/", views.publish_listing, name="publish_listing"),
    path("inventory/", views.inventory, name="inventory"),
    path("inventory/<int:pk>/edit/", views.listing_edit, name="listing_edit"),
    path("inventory/<int:pk>/status/", views.listing_status, name="listing_status"),
    path("inquiries/", views.inquiries, name="inquiries"),
    path("inquiries/<int:pk>/status/", views.inquiry_status, name="inquiry_status"),
    path("partners/", views.partners, name="partners"),
    path("partners/<int:pk>/toggle/", views.partner_toggle, name="partner_toggle"),
    path("locations/", views.locations_manage, name="locations"),
    path("locations/new/", views.locality_edit, name="locality_new"),
    path("locations/<int:pk>/edit/", views.locality_edit, name="locality_edit"),
    path("circle-rates/new/", views.circle_rate_edit, name="circle_rate_new"),
    path("circle-rates/<int:pk>/edit/", views.circle_rate_edit, name="circle_rate_edit"),
]
