"""Helpers for breadcrumbs and schema.org JSON-LD blocks."""
from django.conf import settings


def absolute(url):
    if not url:
        return settings.SITE_DOMAIN
    if url.startswith("http"):
        return url
    return settings.SITE_DOMAIN.rstrip("/") + url


def crumbs(*items):
    """crumbs(("Sell Land", "/sell-land-in-agra/"), ("Fatehabad Road", None))"""
    return [{"name": name, "url": url} for name, url in items]


def breadcrumb_schema(items):
    elements = [{"@type": "ListItem", "position": 1, "name": "Home", "item": absolute("/")}]
    for index, item in enumerate(items, start=2):
        entry = {"@type": "ListItem", "position": index, "name": item["name"]}
        if item.get("url"):
            entry["item"] = absolute(item["url"])
        elements.append(entry)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": elements}


def faq_schema(faqs):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq.question,
                "acceptedAnswer": {"@type": "Answer", "text": faq.answer},
            }
            for faq in faqs
        ],
    }


def business_schema():
    return {
        "@context": "https://schema.org",
        "@type": ["RealEstateAgent", "LocalBusiness"],
        "name": settings.SITE_NAME,
        "description": settings.SITE_TAGLINE,
        "url": absolute("/"),
        "telephone": settings.SITE_PHONE,
        "email": settings.SITE_EMAIL,
        "image": absolute(settings.STATIC_URL + "img/og-default.png"),
        "priceRange": "₹₹",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "Fatehabad Road",
            "addressLocality": "Agra",
            "addressRegion": "Uttar Pradesh",
            "postalCode": "282001",
            "addressCountry": "IN",
        },
        "geo": {"@type": "GeoCoordinates", "latitude": settings.SITE_LAT, "longitude": settings.SITE_LNG},
        "areaServed": {"@type": "City", "name": "Agra"},
        "openingHours": "Mo-Sa 09:30-19:00",
    }
