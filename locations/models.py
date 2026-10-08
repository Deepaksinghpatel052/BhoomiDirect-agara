from decimal import Decimal

from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from submissions.constants import CircleCategory


class Tehsil(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Locality(models.Model):
    class LocalityType(models.TextChoices):
        URBAN = "urban", "Urban Colony"
        HIGHWAY = "highway", "Highway Belt"
        VILLAGE = "village", "Village / Rural"

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    tehsil = models.ForeignKey(Tehsil, on_delete=models.PROTECT, related_name="localities")
    locality_type = models.CharField(max_length=10, choices=LocalityType.choices, default=LocalityType.URBAN)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    description = models.TextField(blank=True)
    connectivity = models.TextField(blank=True, help_text="One point per line")
    landmarks = models.TextField(blank=True, help_text="Nearby landmarks, one per line")
    is_featured = models.BooleanField(default=False)
    image = models.ImageField(upload_to="localities/", blank=True)
    # SEO
    meta_title = models.CharField(max_length=160, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "localities"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("locations:locality", args=[self.slug])

    @property
    def seo_title(self):
        return self.meta_title or f"Sell Land in {self.name}, Agra | Plot & Agricultural Land Buyers"

    @property
    def seo_description(self):
        return self.meta_description or (
            f"Want to sell your plot or land in {self.name}, Agra? Get a free evaluation, "
            f"fair offer and fast payment directly. No brokers, no commission."
        )

    @property
    def connectivity_list(self):
        return [line.strip() for line in self.connectivity.splitlines() if line.strip()]

    @property
    def landmark_list(self):
        return [line.strip() for line in self.landmarks.splitlines() if line.strip()]

    def rate_for(self, category):
        return self.circle_rates.filter(property_type=category).order_by("-effective_year").first()


class CircleRate(models.Model):
    """SAMPLE circle rates for the demo. These are NOT official government figures."""

    locality = models.ForeignKey(Locality, on_delete=models.CASCADE, related_name="circle_rates")
    property_type = models.CharField(max_length=20, choices=CircleCategory.choices)
    rate_per_sq_meter = models.DecimalField(max_digits=10, decimal_places=2)
    effective_year = models.PositiveIntegerField(default=2026)
    is_sample = models.BooleanField(default=True, help_text="Demo data, not official")

    class Meta:
        ordering = ["locality__name", "property_type"]
        unique_together = ("locality", "property_type", "effective_year")

    def __str__(self):
        return f"{self.locality} - {self.get_property_type_display()} ({self.effective_year})"

    @property
    def rate_per_sq_yard(self):
        return self.rate_per_sq_meter * Decimal("0.83612736")


class LocalityFAQ(models.Model):
    locality = models.ForeignKey(Locality, on_delete=models.CASCADE, related_name="faqs")
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "locality FAQ"

    def __str__(self):
        return self.question
