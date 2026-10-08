from django.conf import settings
from django.db import models

from accounts.models import indian_phone_validator


class ChannelPartner(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="partner_profile"
    )
    name = models.CharField(max_length=100)
    firm_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=10, validators=[indian_phone_validator])
    email = models.EmailField(blank=True)
    areas_covered = models.ManyToManyField("locations.Locality", blank=True, related_name="partners")
    rera_agent_number = models.CharField("RERA agent number (optional)", max_length=40, blank=True)
    experience_years = models.PositiveSmallIntegerField(default=0)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.firm_name})" if self.firm_name else self.name

    @property
    def referral_count(self):
        return self.owner_referrals.count() + self.buyer_referrals.count()
