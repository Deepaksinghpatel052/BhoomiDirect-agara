from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("how-it-works/", views.how_it_works, name="how_it_works"),
    path("faq/", views.faq, name="faq"),
    path("contact/", views.contact, name="contact"),
    path("privacy-policy/", views.privacy, name="privacy"),
    path("terms/", views.terms, name="terms"),
    path("demo-feature/", views.demo_notice, name="demo_notice"),
    path("photo-credits/", views.photo_credits, name="photo_credits"),
]
