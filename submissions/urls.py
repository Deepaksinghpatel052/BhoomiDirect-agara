from django.urls import path

from . import views

app_name = "submissions"

urlpatterns = [
    path("sell-your-property/", views.sell_start, name="sell"),
    path("sell-your-property/quick/", views.quick_lead, name="quick_lead"),
    path("sell-your-property/restart/", views.sell_restart, name="sell_restart"),
    path("sell-your-property/step/<int:step>/", views.sell_step, name="sell_step"),
    path("sell-your-property/verify/", views.sell_verify, name="sell_verify"),
    path("sell-your-property/thank-you/<str:reference>/", views.thank_you, name="thank_you"),
    path("track-submission/", views.track, name="track"),
    # Owner portal
    path("my/", views.owner_dashboard, name="owner_dashboard"),
    path("my/submissions/<str:reference>/", views.owner_submission, name="owner_submission"),
    path("my/submissions/<str:reference>/upload/", views.owner_upload, name="owner_upload"),
    path("my/offers/<int:pk>/respond/", views.offer_respond, name="offer_respond"),
    path("my/notifications/", views.notifications, name="notifications"),
    path("documents/<int:pk>/", views.document_download, name="document_download"),
]
