from django.test import TestCase
from django.urls import reverse

from core.templatetags.site_tags import indian_grouping, inr, inr_short
from listings.models import Listing

from .helpers import make_locality


class IndianFormatTests(TestCase):
    def test_indian_grouping(self):
        self.assertEqual(indian_grouping(4500000), "45,00,000")
        self.assertEqual(indian_grouping(123), "123")
        self.assertEqual(indian_grouping(12345678), "1,23,45,678")

    def test_inr_filters(self):
        self.assertEqual(inr(4500000), "₹ 45,00,000")
        self.assertEqual(inr_short(4500000), "₹ 45 Lakh")
        self.assertEqual(inr_short(12000000), "₹ 1.2 Crore")
        self.assertEqual(inr_short(85000), "₹ 85,000")
        self.assertEqual(inr(None), "—")


class PublicPagesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.locality = make_locality()

    def test_public_pages_render(self):
        for name in ("core:home", "core:about", "core:faq", "core:contact", "core:how_it_works",
                     "locations:estimator", "locations:area_index", "locations:sell_plot",
                     "locations:sell_agricultural", "listings:list", "blog:list", "partners:join"):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_locality_landing_page_has_seo(self):
        response = self.client.get(self.locality.get_absolute_url())
        self.assertContains(response, "Sell Your Land or Plot in Fatehabad Road")
        self.assertContains(response, "application/ld+json")
        self.assertContains(response, "Sample rates for demo, not official")
        self.assertContains(response, 'rel="canonical"')

    def test_sitemap_and_robots(self):
        self.assertContains(self.client.get("/sitemap.xml"), "/sell-land-in-agra/fatehabad-road/")
        robots = self.client.get("/robots.txt")
        self.assertContains(robots, "Disallow: /dashboard/")
        self.assertContains(robots, "Sitemap:")

    def test_estimator_api(self):
        url = reverse("locations:estimator_api")
        response = self.client.get(url, {"locality": self.locality.pk, "property_type": "residential_plot", "area_value": 200, "area_unit": "sqyard"})
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertIn("Lakh", data["low"])

    def test_404_page(self):
        response = self.client.get("/no-such-page/")
        self.assertEqual(response.status_code, 404)

    def test_contact_form_saves(self):
        response = self.client.post(reverse("core:contact"), {"name": "A", "phone": "9876543210", "message": "Hi"})
        self.assertEqual(response.status_code, 302)

    def test_listing_page_empty_state(self):
        self.assertEqual(Listing.objects.count(), 0)
        self.assertContains(self.client.get(reverse("listings:list")), "No properties match")
