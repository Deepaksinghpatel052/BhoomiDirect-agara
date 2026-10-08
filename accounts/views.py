from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from submissions.models import PropertySubmission

from .forms import LoginForm, SignupForm


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


def signup(request):
    if request.user.is_authenticated:
        return redirect("accounts:after_login")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        # Link any earlier submissions made with this phone number.
        PropertySubmission.objects.filter(phone=user.phone, owner_user__isnull=True).update(owner_user=user)
        login(request, user, backend="accounts.backends.PhoneEmailUsernameBackend")
        messages.success(request, "Welcome! Your owner account is ready.")
        return redirect("submissions:owner_dashboard")
    return render(request, "accounts/signup.html", {"form": form})


@login_required
def after_login(request):
    """Send each role to its own home after login."""
    user = request.user
    if user.is_company_staff:
        return redirect("dashboard:overview")
    if user.is_partner:
        return redirect("partners:portal")
    return redirect("submissions:owner_dashboard")
