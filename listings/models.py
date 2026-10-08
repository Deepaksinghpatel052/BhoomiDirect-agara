from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from locations.units import all_units, to_sq_meter, trim_number
from submissions.constants import AreaUnit, PropertyType


class Listing(models.Model):
    class ListingStatus(models.TextChoices):
        AVAILABLE = "available", "Available"
        BOOKED = "booked", "Booked"
        SOLD = "sold", "Sold"

    acquisition = models.OneToOneField(
        "acquisitions.Acquisition", on_delete=models.SET_NULL, null=True, blank=True, related_name="listing"
    )
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=14, decimal_places=2)
    area_value = models.DecimalField(max_digits=12, decimal_places=2)
    area_unit = models.CharField(max_length=10, choices=AreaUnit.choices, default=AreaUnit.SQYARD)
    area_sq_meter = models.DecimalField(max_digits=14, decimal_places=2, editable=False, default=0)
    property_type = models.CharField(max_length=30, choices=PropertyType.choices)
    locality = models.ForeignKey("locations.Locality", on_delete=models.PROTECT, related_name="listings")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    features = models.TextField(blank=True, help_text="One feature per line")
    road_width_ft = models.PositiveIntegerField(null=True, blank=True)
    facing = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=10, choices=ListingStatus.choices, default=ListingStatus.AVAILABLE)
    is_featured = models.BooleanField(default=False)
    sold_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    sold_date = models.DateField(null=True, blank=True)
    meta_title = models.CharField(max_length=160, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_featured", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.area_sq_meter = to_sq_meter(self.area_value, self.area_unit) or 0
        if not self.slug:
            base = slugify(self.title)[:180]
            slug, n = base, 2
            while Listing.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = f"{base}-{n}", n + 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("listings:detail", args=[self.slug])

    @property
    def seo_title(self):
        return self.meta_title or f"{self.title} | {settings.SITE_NAME}"

    @property
    def seo_description(self):
        return self.meta_description or self.description[:155]

    @property
    def area_display(self):
        value = trim_number(self.area_value)
        return f"{value} {self.get_area_unit_display()}"

    @property
    def area_in_units(self):
        return all_units(self.area_sq_meter) if self.area_sq_meter else {}

    @property
    def feature_list(self):
        return [line.strip() for line in self.features.splitlines() if line.strip()]

    @property
    def cover(self):
        return self.photos.first()

    @property
    def price_per_sqyard(self):
        if not self.area_sq_meter:
            return None
        return round(self.price / (self.area_sq_meter / to_sq_meter(1, "sqyard")))

    @property
    def profit(self):
        if self.status != self.ListingStatus.SOLD or not self.sold_price or not self.acquisition:
            return None
        return self.sold_price - self.acquisition.total_cost

    @property
    def expected_margin_percent(self):
        if not self.acquisition or not self.acquisition.total_cost:
            return None
        return round(float((self.price - self.acquisition.total_cost) * 100 / self.acquisition.total_cost), 1)

    @property
    def status_css(self):
        return {"available": "success", "booked": "warning", "sold": "secondary"}[self.status]


class ListingPhoto(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="listings/")
    alt_text = models.CharField(max_length=150, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.alt_text or f"Photo {self.pk}"


class BuyerInquiry(models.Model):
    class InquiryStatus(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        SITE_VISIT = "site_visit", "Site visit done"
        NEGOTIATING = "negotiating", "Negotiating"
        CLOSED = "closed", "Deal closed"
        LOST = "lost", "Not interested"

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="inquiries")
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=10)
    email = models.EmailField(blank=True)
    budget = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=InquiryStatus.choices, default=InquiryStatus.NEW)
    referred_by = models.ForeignKey(
        "partners.ChannelPartner", on_delete=models.SET_NULL, null=True, blank=True, related_name="buyer_referrals"
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "buyer inquiries"

    def __str__(self):
        return f"{self.name} - {self.listing}"
