from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

indian_phone_validator = RegexValidator(
    regex=r"^[6-9]\d{9}$",
    message="Enter a valid 10 digit Indian mobile number starting with 6, 7, 8 or 9.",
)


class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = "owner", "Property Owner"
        FIELD_AGENT = "field_agent", "Field Agent"
        EVALUATOR = "evaluator", "Evaluator"
        ADMIN = "admin", "Admin"
        CHANNEL_PARTNER = "channel_partner", "Channel Partner"
        BUYER = "buyer", "Buyer"

    STAFF_ROLES = (Role.ADMIN, Role.EVALUATOR, Role.FIELD_AGENT)

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.OWNER)
    phone = models.CharField(
        max_length=10, unique=True, null=True, blank=True, validators=[indian_phone_validator]
    )
    whatsapp = models.CharField(max_length=10, blank=True)
    city = models.CharField(max_length=80, blank=True, default="Agra")

    class Meta:
        ordering = ["first_name", "username"]

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    @property
    def is_company_staff(self):
        return self.is_superuser or self.role in self.STAFF_ROLES

    @property
    def is_admin_role(self):
        return self.is_superuser or self.role == self.Role.ADMIN

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER

    @property
    def is_partner(self):
        return self.role == self.Role.CHANNEL_PARTNER

    def has_any_role(self, *roles):
        return self.is_superuser or self.role in roles


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=150)
    message = models.TextField(blank=True)
    url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.title}"
