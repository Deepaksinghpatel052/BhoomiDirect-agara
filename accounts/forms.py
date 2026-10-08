from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User, indian_phone_validator


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Mobile number, email or username",
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg", "autofocus": True}),
    )
    password = forms.CharField(
        label="Password", widget=forms.PasswordInput(attrs={"class": "form-control form-control-lg"})
    )


class SignupForm(UserCreationForm):
    first_name = forms.CharField(label="Full name", max_length=150)
    phone = forms.CharField(label="Mobile number", max_length=10, validators=[indian_phone_validator])
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ("first_name", "phone", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control form-control-lg")
        self.fields["phone"].widget.attrs.update({"inputmode": "numeric", "data-phone": "1"})

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("An account with this mobile number already exists. Please log in.")
        return phone

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["phone"]
        user.role = User.Role.OWNER
        user.whatsapp = self.cleaned_data["phone"]
        if commit:
            user.save()
        return user
