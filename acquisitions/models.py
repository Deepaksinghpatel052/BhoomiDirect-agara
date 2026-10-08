from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from submissions.constants import PROPERTY_TO_CIRCLE
from submissions.models import PropertySubmission

score_validators = [MinValueValidator(1), MaxValueValidator(10)]


class SiteVisit(models.Model):
    class VisitStatus(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    submission = models.ForeignKey(PropertySubmission, on_delete=models.CASCADE, related_name="site_visits")
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="site_visits"
    )
    scheduled_for = models.DateTimeField()
    status = models.CharField(max_length=10, choices=VisitStatus.choices, default=VisitStatus.SCHEDULED)
    visit_notes = models.TextField(blank=True)
    # Ground reality checks
    boundary_matches_documents = models.BooleanField(default=False)
    road_access_confirmed = models.BooleanField(default=False)
    no_encroachment = models.BooleanField(default=False)
    owner_met_in_person = models.BooleanField(default=False)
    neighbour_feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-scheduled_for"]

    def __str__(self):
        return f"Visit {self.submission.reference_id} on {self.scheduled_for:%d %b %Y}"

    @property
    def checks_passed(self):
        return sum(
            [
                self.boundary_matches_documents,
                self.road_access_confirmed,
                self.no_encroachment,
                self.owner_met_in_person,
            ]
        )


class SiteVisitPhoto(models.Model):
    visit = models.ForeignKey(SiteVisit, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="site_visits/")
    uploaded_at = models.DateTimeField(auto_now_add=True)


class Evaluation(models.Model):
    class Recommendation(models.TextChoices):
        STRONG_BUY = "strong_buy", "Strong Buy"
        CONSIDER = "consider", "Consider"
        REJECT = "reject", "Reject"

    SCORE_FIELDS = (
        "location_potential",
        "road_access",
        "legal_clarity",
        "price_vs_market",
        "resale_demand",
        "development_nearby",
    )
    MAX_SCORE = 60
    STRONG_BUY_MIN = 45
    CONSIDER_MIN = 30

    submission = models.OneToOneField(PropertySubmission, on_delete=models.CASCADE, related_name="evaluation")
    evaluator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    location_potential = models.PositiveSmallIntegerField(default=5, validators=score_validators)
    road_access = models.PositiveSmallIntegerField(default=5, validators=score_validators)
    legal_clarity = models.PositiveSmallIntegerField(default=5, validators=score_validators)
    price_vs_market = models.PositiveSmallIntegerField(default=5, validators=score_validators)
    resale_demand = models.PositiveSmallIntegerField(default=5, validators=score_validators)
    development_nearby = models.PositiveSmallIntegerField(default=5, validators=score_validators)
    total_score = models.PositiveSmallIntegerField(default=0, editable=False)
    recommendation = models.CharField(max_length=12, choices=Recommendation.choices, blank=True, editable=False)
    circle_rate_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, editable=False)
    estimated_resale_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    remarks = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Evaluation {self.submission.reference_id}: {self.total_score}/60"

    @classmethod
    def calculate(cls, scores):
        """Return (total, recommendation) for an iterable of six 1-10 scores."""
        total = sum(int(s) for s in scores)
        if total >= cls.STRONG_BUY_MIN:
            rec = cls.Recommendation.STRONG_BUY
        elif total >= cls.CONSIDER_MIN:
            rec = cls.Recommendation.CONSIDER
        else:
            rec = cls.Recommendation.REJECT
        return total, rec

    def save(self, *args, **kwargs):
        self.total_score, self.recommendation = self.calculate(getattr(self, f) for f in self.SCORE_FIELDS)
        self.circle_rate_value = self.compute_circle_value()
        super().save(*args, **kwargs)

    def compute_circle_value(self):
        sub = self.submission
        if not (sub.locality_id and sub.area_sq_meter):
            return None
        rate = sub.locality.rate_for(PROPERTY_TO_CIRCLE.get(sub.property_type))
        if not rate:
            return None
        return (rate.rate_per_sq_meter * sub.area_sq_meter).quantize(Decimal("1"))

    @property
    def score_percent(self):
        return round(self.total_score * 100 / self.MAX_SCORE)

    @property
    def buy_price(self):
        """Latest offer amount if any, otherwise owner's expected price."""
        offer = self.submission.offers.order_by("-created_at").first()
        return offer.amount if offer else self.submission.expected_price

    @property
    def margin_percent(self):
        price = self.buy_price
        if not price or not self.estimated_resale_value:
            return None
        return round(float((self.estimated_resale_value - price) * 100 / price), 1)

    @property
    def recommendation_css(self):
        return {"strong_buy": "success", "consider": "warning", "reject": "danger"}.get(self.recommendation, "secondary")


class LegalChecklist(models.Model):
    ITEMS = (
        ("title_verified", "Title chain verified (30 years)"),
        ("khatauni_matched", "Khatauni matches seller name"),
        ("no_encumbrance", "No encumbrance / loan found"),
        ("mutation_verified", "Mutation (Dakhil Kharij) verified"),
        ("owner_id_verified", "Owner Aadhaar / PAN verified"),
        ("noc_obtained", "NOC obtained (if needed)"),
    )

    submission = models.OneToOneField(PropertySubmission, on_delete=models.CASCADE, related_name="legal_checklist")
    title_verified = models.BooleanField(default=False)
    khatauni_matched = models.BooleanField(default=False)
    no_encumbrance = models.BooleanField(default=False)
    mutation_verified = models.BooleanField(default=False)
    owner_id_verified = models.BooleanField(default=False)
    noc_obtained = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Legal checklist {self.submission.reference_id}"

    @property
    def done_count(self):
        return sum(getattr(self, key) for key, _ in self.ITEMS)

    @property
    def progress(self):
        return round(self.done_count * 100 / len(self.ITEMS))

    @property
    def item_states(self):
        return [(key, label, getattr(self, key)) for key, label in self.ITEMS]


class Offer(models.Model):
    class OfferStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        COUNTERED = "countered", "Countered"

    submission = models.ForeignKey(PropertySubmission, on_delete=models.CASCADE, related_name="offers")
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(1)])
    valid_till = models.DateField()
    terms = models.TextField(blank=True, default="Full payment at registry. Company bears registry assistance.")
    status = models.CharField(max_length=10, choices=OfferStatus.choices, default=OfferStatus.PENDING)
    owner_counter_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    owner_note = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Offer {self.amount} for {self.submission.reference_id}"

    @property
    def is_open(self):
        return self.status == self.OfferStatus.PENDING and self.valid_till >= timezone.localdate()

    @property
    def status_css(self):
        return {"pending": "warning", "accepted": "success", "rejected": "danger", "countered": "info"}[self.status]


class Acquisition(models.Model):
    class PaymentMode(models.TextChoices):
        RTGS = "rtgs", "RTGS / NEFT"
        CHEQUE = "cheque", "Cheque / DD"
        MIXED = "mixed", "Part RTGS, part cheque"

    submission = models.OneToOneField(PropertySubmission, on_delete=models.PROTECT, related_name="acquisition")
    purchase_price = models.DecimalField(max_digits=14, decimal_places=2)
    purchase_date = models.DateField(default=timezone.localdate)
    registry_date = models.DateField(null=True, blank=True)
    payment_mode = models.CharField(max_length=10, choices=PaymentMode.choices, default=PaymentMode.RTGS)
    stamp_duty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    registration_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_costs = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0, editable=False)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-purchase_date"]

    def __str__(self):
        return f"Acquired {self.submission.reference_id}"

    def save(self, *args, **kwargs):
        self.total_cost = self.purchase_price + self.stamp_duty + self.registration_fee + self.other_costs
        super().save(*args, **kwargs)

    @property
    def listing_or_none(self):
        return getattr(self, "listing", None)


class ActivityLog(models.Model):
    submission = models.ForeignKey(
        PropertySubmission, on_delete=models.CASCADE, null=True, blank=True, related_name="activities"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=120)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.action} ({self.created_at:%d %b %Y %H:%M})"


class InternalNote(models.Model):
    submission = models.ForeignKey(PropertySubmission, on_delete=models.CASCADE, related_name="internal_notes")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.text[:50]
