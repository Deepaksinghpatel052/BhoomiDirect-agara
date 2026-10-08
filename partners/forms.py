from django import forms
from django.contrib.auth.password_validation import validate_password

from accounts.models import User, indian_phone_validator
from core.forms import BootstrapFormMixin
from listings.models import Listing
from locations.models import Locality
from submissions.constants import PropertyType

from .models import ChannelPartner


class PartnerRegistrationForm(BootstrapFormMixin, forms.ModelForm):
    areas_covered = forms.ModelMultipleChoiceField(
        queryset=Locality.objects.all(), widget=forms.SelectMultiple(attrs={"size": 6}), required=False
    )
    password = forms.CharField(
        widget=forms.PasswordInput, help_text="Used to log in to the partner portal after approval."
    )

    class Meta:
        model = ChannelPartner
        fields = ("name", "firm_name", "phone", "email", "areas_covered", "rera_agent_number", "experience_years")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
        self.fields["areas_covered"].widget.attrs["class"] = "form-select"
        self.fields["phone"].widget.attrs.update({"inputmode": "numeric", "data-phone": "1"})

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if User.objects.filter(phone=phone).exists() or ChannelPartner.objects.filter(phone=phone).exists():
            raise forms.ValidationError("This mobile number is already registered.")
        return phone

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def save(self, commit=True):
        partner = super().save(commit=False)
        user = User.objects.create_user(
            username=partner.phone,
            password=self.cleaned_data["password"],
            first_name=partner.name,
            email=partner.email,
            phone=partner.phone,
            role=User.Role.CHANNEL_PARTNER,
        )
        partner.user = user
        partner.save()
        self.save_m2m()
        return partner


class ReferOwnerForm(BootstrapFormMixin, forms.Form):
    owner_name = forms.CharField(max_length=120)
    phone = forms.CharField(label="Owner mobile", max_length=10, validators=[indian_phone_validator])
    property_type = forms.ChoiceField(choices=PropertyType.choices)
    locality = forms.ModelChoiceField(queryset=Locality.objects.all())
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class ReferBuyerForm(BootstrapFormMixin, forms.Form):
    listing = forms.ModelChoiceField(queryset=Listing.objects.filter(status=Listing.ListingStatus.AVAILABLE))
    name = forms.CharField(label="Buyer name", max_length=100)
    phone = forms.CharField(label="Buyer mobile", max_length=10, validators=[indian_phone_validator])
    budget = forms.DecimalField(required=False, max_digits=14, decimal_places=2)
    message = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
