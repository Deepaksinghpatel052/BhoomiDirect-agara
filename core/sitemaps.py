from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from blog.models import Post
from listings.models import Listing
from locations.models import Locality


class StaticSitemap(Sitemap):
    changefreq = "weekly"

    PAGES = {
        "core:home": 1.0,
        "submissions:sell": 0.95,
        "locations:estimator": 0.9,
        "locations:sell_plot": 0.9,
        "locations:sell_agricultural": 0.9,
        "locations:sell_commercial": 0.9,
        "locations:area_index": 0.8,
        "listings:list": 0.8,
        "core:how_it_works": 0.7,
        "core:about": 0.6,
        "core:faq": 0.6,
        "core:contact": 0.6,
        "partners:join": 0.5,
        "blog:list": 0.7,
        "submissions:track": 0.4,
        "core:privacy": 0.2,
        "core:terms": 0.2,
    }

    def items(self):
        return list(self.PAGES)

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return self.PAGES[item]


class LocalitySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.85

    def items(self):
        return Locality.objects.all()


class ListingSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.7

    def items(self):
        return Listing.objects.exclude(status=Listing.ListingStatus.SOLD)

    def lastmod(self, obj):
        return obj.updated_at


class PostSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return Post.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at


sitemaps = {
    "static": StaticSitemap,
    "localities": LocalitySitemap,
    "listings": ListingSitemap,
    "blog": PostSitemap,
}
