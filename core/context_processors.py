from django.conf import settings


def site_context(request):
    unread = 0
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        unread = user.notifications.filter(is_read=False).count()
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_TAGLINE": settings.SITE_TAGLINE,
        "SITE_PHONE": settings.SITE_PHONE,
        "SITE_PHONE_RAW": settings.SITE_PHONE_RAW,
        "SITE_WHATSAPP": settings.SITE_WHATSAPP,
        "SITE_EMAIL": settings.SITE_EMAIL,
        "SITE_ADDRESS": settings.SITE_ADDRESS,
        "SITE_DOMAIN": settings.SITE_DOMAIN.rstrip("/"),
        "unread_notifications": unread,
        "footer_localities": _footer_localities(),
    }


def _footer_localities():
    from locations.models import Locality

    return list(Locality.objects.only("name", "slug").order_by("-is_featured", "name")[:12])
