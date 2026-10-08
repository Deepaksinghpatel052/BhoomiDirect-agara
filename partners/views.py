from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from core.seo import crumbs
from listings.models import BuyerInquiry, Listing
from submissions.constants import Status
from submissions.models import PropertySubmission, StatusHistory
from submissions.services import log_activity

from .forms import PartnerRegistrationForm, ReferBuyerForm, ReferOwnerForm


def join(request):
    form = PartnerRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(
            request,
            "Registration received! Our team will verify and approve your account within 48 hours. "
            "You can log in with your mobile number after approval.",
        )
        return redirect("partners:join")
    return render(
        request,
        "partners/join.html",
        {
            "form": form,
            "breadcrumbs": crumbs(("Channel Partners", None)),
            "page_title": "Become a Channel Partner | Property Brokers in Agra",
            "meta_description": "Join the BhoomiDirect Agra channel partner network. Refer land owners and buyers, earn transparent commission.",
        },
    )


def _partner_or_403(request):
    profile = getattr(request.user, "partner_profile", None)
    if not request.user.is_partner or profile is None:
        raise PermissionDenied("Channel partner access only.")
    return profile


@login_required
def portal(request):
    partner = _partner_or_403(request)
    return render(
        request,
        "partners/portal.html",
        {
            "partner": partner,
            "listings": Listing.objects.filter(status=Listing.ListingStatus.AVAILABLE).select_related("locality"),
            "owner_form": ReferOwnerForm(),
            "buyer_form": ReferBuyerForm(),
            "owner_referrals": partner.owner_referrals.select_related("locality")[:20],
            "buyer_referrals": partner.buyer_referrals.select_related("listing")[:20],
        },
    )


@login_required
@require_POST
def refer_owner(request):
    partner = _partner_or_403(request)
    if not partner.is_approved:
        messages.error(request, "Your partner account is awaiting approval.")
        return redirect("partners:portal")
    form = ReferOwnerForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        submission = PropertySubmission.objects.create(
            owner_name=data["owner_name"],
            phone=data["phone"],
            whatsapp=data["phone"],
            property_type=data["property_type"],
            locality=data["locality"],
            tehsil=data["locality"].tehsil,
            reason_for_selling=data["notes"],
            source=PropertySubmission.Source.PARTNER,
            referred_by=partner,
        )
        StatusHistory.objects.create(submission=submission, new_status=Status.NEW, note=f"Referred by {partner}")
        log_activity(submission, request.user, "Owner referred by channel partner", str(partner))
        messages.success(request, f"Owner lead {submission.reference_id} created. Thank you!")
    else:
        messages.error(request, "Please check the owner referral form.")
    return redirect("partners:portal")


@login_required
@require_POST
def refer_buyer(request):
    partner = _partner_or_403(request)
    if not partner.is_approved:
        messages.error(request, "Your partner account is awaiting approval.")
        return redirect("partners:portal")
    form = ReferBuyerForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        BuyerInquiry.objects.create(
            listing=data["listing"],
            name=data["name"],
            phone=data["phone"],
            budget=data["budget"],
            message=data["message"],
            referred_by=partner,
        )
        messages.success(request, "Buyer referral submitted. Our sales team will coordinate with you.")
    else:
        messages.error(request, "Please check the buyer referral form.")
    return redirect("partners:portal")
