from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, re_path
from django.views.static import serve

from core.sitemaps import sitemaps
from core import views as core_views

admin.site.site_header = f"{settings.SITE_NAME} Admin"
admin.site.site_title = settings.SITE_NAME
admin.site.index_title = "Back office"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("robots.txt", core_views.robots_txt, name="robots_txt"),
    path("healthz/", core_views.healthz, name="healthz"),
    path("accounts/", include("accounts.urls")),
    path("dashboard/", include("acquisitions.urls")),
    path("blog/", include("blog.urls")),
    path("", include("submissions.urls")),
    path("", include("listings.urls")),
    path("", include("partners.urls")),
    path("", include("locations.urls")),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif settings.SERVE_MEDIA:
    # Production without Nginx: let Django/Gunicorn serve public media (photos).
    # Private title documents are never under MEDIA_ROOT.
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]

handler403 = "core.views.error_403"
handler404 = "core.views.error_404"
handler500 = "core.views.error_500"
