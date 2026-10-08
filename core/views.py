import json
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from acquisitions.models import Acquisition
from locations.models import Locality
from submissions.constants import PROPERTY_TYPE_ICONS, PropertyType
from submissions.forms import QuickLeadForm

from .forms import ContactForm
from .models import FAQ, SiteSettings, Testimonial
from .seo import business_schema, crumbs, faq_schema

PROPERTY_TYPE_INFO = {
    PropertyType.RESIDENTIAL_PLOT: ("Plots in colonies, ADA layouts and gated societies.", "locations:sell_plot"),
    PropertyType.COMMERCIAL_PLOT: ("Shops, showroom plots and highway-facing land.", "locations:sell_commercial"),
    PropertyType.AGRICULTURAL_LAND: ("Khet, farmland and bigha-size land in any tehsil.", "locations:sell_agricultural"),
    PropertyType.FARMHOUSE_LAND: ("Land suitable for farmhouses near expressways.", "locations:sell_agricultural"),
    PropertyType.INDUSTRIAL_LAND: ("Land near industrial areas and logistics routes.", "locations:sell_commercial"),
    PropertyType.OLD_CONSTRUCTION: ("Old house or structure? We buy it as a plot.", "locations:sell_plot"),
}


def property_type_cards():
    return [
        {
            "value": value,
            "label": label,
            "icon": PROPERTY_TYPE_ICONS[value],
            "desc": PROPERTY_TYPE_INFO[value][0],
            "url": reverse(PROPERTY_TYPE_INFO[value][1]),
        }
        for value, label in PropertyType.choices
    ]


def map_points(localities):
    return [
        {
            "name": loc.name,
            "lat": float(loc.latitude),
            "lng": float(loc.longitude),
            "url": loc.get_absolute_url(),
            "type": loc.get_locality_type_display(),
        }
        for loc in localities
    ]


def home(request):
    localities = Locality.objects.select_related("tehsil").all()
    home_faqs = FAQ.objects.filter(show_on_home=True)[:6]
    schemas = [business_schema()]
    if home_faqs:
        schemas.append(faq_schema(home_faqs))
    context = {
        "quick_form": QuickLeadForm(),
        "stats": SiteSettings.load(),
        "property_types": property_type_cards(),
        "featured_localities": [loc for loc in localities if loc.is_featured][:8],
        "map_points": map_points(localities),
        "recent_acquisitions": Acquisition.objects.select_related("submission__locality").order_by("-purchase_date")[:4],
        "testimonials": Testimonial.objects.filter(is_active=True)[:6],
        "faqs": home_faqs,
        "schemas": schemas,
    }
    return render(request, "core/home.html", context)


def static_page(template, title, description, crumb_title=None):
    def view(request):
        context = {
            "page_title": title,
            "meta_description": description,
            "breadcrumbs": crumbs((crumb_title or title, None)),
        }
        return render(request, template, context)

    return view


about = static_page(
    "core/about.html",
    "About Us",
    "BhoomiDirect Agra buys plots, agricultural land and farmhouse land directly from owners in Agra.",
)
how_it_works = static_page(
    "core/how_it_works.html",
    "How It Works",
    "Five simple steps to sell your land in Agra: submit, free evaluation, site visit, fair offer, registry & payment.",
)
privacy = static_page("core/privacy.html", "Privacy Policy", "How BhoomiDirect Agra handles your personal data.")
terms = static_page("core/terms.html", "Terms of Use", "Terms of using the BhoomiDirect Agra website.")


def faq(request):
    faqs = FAQ.objects.all()
    grouped = {}
    for item in faqs:
        grouped.setdefault(item.get_category_display(), []).append(item)
    return render(
        request,
        "core/faq.html",
        {
            "grouped_faqs": grouped,
            "breadcrumbs": crumbs(("FAQ", None)),
            "schemas": [faq_schema(faqs)] if faqs else [],
        },
    )


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Thank you! Our team will call you back within 24 hours.")
        return redirect("core:contact")
    return render(
        request,
        "core/contact.html",
        {
            "form": form,
            "breadcrumbs": crumbs(("Contact", None)),
            "office": {"lat": settings.SITE_LAT, "lng": settings.SITE_LNG},
        },
    )


def photo_credits(request):
    """Attribution for the CC BY / CC BY-SA photographs used in the demo."""
    path = Path(settings.BASE_DIR) / "static" / "img" / "photos" / "credits.json"
    credits = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    return render(
        request,
        "core/photo_credits.html",
        {
            "credits": credits,
            "page_title": "Photo Credits",
            "meta_description": "Attribution for the photographs used on this website.",
            "breadcrumbs": crumbs(("Photo Credits", None)),
        },
    )


def demo_notice(request):
    """Target for buttons that are intentionally not wired in the demo."""
    messages.info(request, "Demo: this feature is planned for the full version (see Future Scope).")
    return redirect(request.META.get("HTTP_REFERER") or "core:home")


@require_GET
def healthz(request):
    """Used by Docker / load balancers: checks the app and the database."""
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return HttpResponse("ok", content_type="text/plain")


@require_GET
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /dashboard/",
        "Disallow: /admin/",
        "Disallow: /my/",
        "Disallow: /accounts/",
        "Disallow: /partner/",
        "Allow: /",
        "",
        f"Sitemap: {settings.SITE_DOMAIN.rstrip('/')}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def error_404(request, exception=None):
    return render(request, "404.html", status=404)


def error_403(request, exception=None):
    return render(request, "403.html", {"reason": str(exception or "")}, status=403)


def error_500(request):
    return render(request, "500.html", status=500)
