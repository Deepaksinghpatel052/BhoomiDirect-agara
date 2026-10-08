from django.db import models


class SiteSettings(models.Model):
    """Singleton for editable homepage trust stats and contact details."""

    properties_acquired = models.PositiveIntegerField(default=180)
    acres_evaluated = models.PositiveIntegerField(default=1250)
    payout_crore = models.DecimalField(max_digits=8, decimal_places=1, default=96.5)
    avg_days_to_close = models.PositiveIntegerField(default=21)
    announcement = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "site settings"
        verbose_name_plural = "site settings"

    def __str__(self):
        return "Site settings"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    property_sold = models.CharField(max_length=120, help_text="e.g. 2 Bigha agricultural land")
    quote = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "-id"]

    def __str__(self):
        return f"{self.name} ({self.location})"


class FAQ(models.Model):
    class Category(models.TextChoices):
        SELLING = "selling", "Selling to us"
        LEGAL = "legal", "Legal & documents"
        PAYMENT = "payment", "Price & payment"
        BUYING = "buying", "Buying property"

    category = models.CharField(max_length=20, choices=Category.choices, default=Category.SELLING)
    question = models.CharField(max_length=255)
    answer = models.TextField()
    show_on_home = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["category", "order", "id"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    subject = models.CharField(max_length=150, blank=True)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.subject or 'Enquiry'}"
