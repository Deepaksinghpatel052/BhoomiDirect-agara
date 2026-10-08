import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from acquisitions.models import Offer
from core.seo import crumbs
from locations.models import Locality
from locations.units import factors_for_js

from .constants import (
    AGRICULTURAL_TYPES,
    CLOSED_STATUSES,
    OWNER_STATUS_HELP,
    PIPELINE_ORDER,
    PROPERTY_TYPE_ICONS,
    Status,
)
from .forms import (
    OfferResponseForm,
    OTPForm,
    OwnerUploadForm,
    QuickLeadForm,
    Step1OwnerForm,
    Step2LocationForm,
    Step3SizeForm,
    Step4LegalForm,
    Step5PriceForm,
    TrackForm,
)
from .models import PropertySubmission, StatusHistory, SubmissionDocument, SubmissionPhoto
from .services import change_status, log_activity

WIZARD_KEY = "sell_wizard"
STEPS = {
    1: ("Owner Details", Step1OwnerForm),
    2: ("Property Type & Location", Step2LocationForm),
    3: ("Size & Features", Step3SizeForm),
    4: ("Legal Details", Step4LegalForm),
    5: ("Price, Photos & Documents", Step5PriceForm),
}


# --------------------------------------------------------------------------
# Session helpers: each step stores its raw POST data so the user can go back.
# --------------------------------------------------------------------------
def _wizard(request):
    return request.session.setdefault(WIZARD_KEY, {})


def _store_step(request, step, post):
    wizard = _wizard(request)
    wizard[str(step)] = {k: post.getlist(k) for k in post if k != "csrfmiddlewaretoken"}
    request.session.modified = True


def _step_data(request, step):
    raw = _wizard(request).get(str(step))
    if raw is None:
        return None
    data = QueryDict(mutable=True)
    for key, values in raw.items():
        data.setlist(key, values)
    return data


def _phone_verified(request):
    step1 = _step_data(request, 1)
    return bool(step1) and request.session.get("sell_verified_phone") == step1.get("phone")


def _first_missing_step(request, upto):
    for n in range(1, upto):
        if _step_data(request, n) is None:
            return n
    return None


def _wizard_property_type(request):
    step2 = _step_data(request, 2)
    return step2.get("property_type") if step2 else None


# --------------------------------------------------------------------------
# Quick lead (hero form)
# --------------------------------------------------------------------------
@require_POST
def quick_lead(request):
    form = QuickLeadForm(request.POST)
    if not form.is_valid():
        for errors in form.errors.values():
            messages.error(request, errors[0])
        return redirect(request.META.get("HTTP_REFERER") or "core:home")
    data = form.cleaned_data
    locality = data.get("locality")
    submission = PropertySubmission.objects.create(
        owner_name=data["owner_name"],
        phone=data["phone"],
        whatsapp=data["phone"],
        property_type=data["property_type"],
        locality=locality,
        tehsil=locality.tehsil if locality else None,
        owner_user=request.user if request.user.is_authenticated and request.user.is_owner else None,
    )
    StatusHistory.objects.create(submission=submission, new_status=Status.NEW, note="Quick enquiry from website")
    log_activity(submission, request.user, "Quick lead created", "Hero form on website")

    # Pre-fill the full form so the owner can complete the details.
    request.session[WIZARD_KEY] = {
        "quick_id": submission.pk,
        "1": {"owner_name": [data["owner_name"]], "phone": [data["phone"]], "relation": ["owner"]},
    }
    if locality:
        request.session[WIZARD_KEY]["prefill_2"] = {
            "property_type": data["property_type"],
            "tehsil": locality.tehsil_id,
            "locality": locality.pk,
        }
    else:
        request.session[WIZARD_KEY]["prefill_2"] = {"property_type": data["property_type"]}
    messages.success(
        request,
        f"Thank you {data['owner_name']}! Your enquiry {submission.reference_id} is registered. "
        "Complete the details below to get a faster and better offer.",
    )
    return redirect("submissions:sell_step", step=1)


# --------------------------------------------------------------------------
# Multi-step sell form
# --------------------------------------------------------------------------
def sell_start(request):
    return redirect("submissions:sell_step", step=1)


def sell_restart(request):
    request.session.pop(WIZARD_KEY, None)
    request.session.pop("sell_verified_phone", None)
    messages.info(request, "Form cleared. Start fresh.")
    return redirect("submissions:sell_step", step=1)


def sell_step(request, step):
    if step not in STEPS:
        raise Http404
    missing = _first_missing_step(request, step)
    if missing:
        return redirect("submissions:sell_step", step=missing)
    if step > 1 and not _phone_verified(request):
        return redirect("submissions:sell_verify")

    title, form_class = STEPS[step]
    if request.method == "POST":
        form = form_class(request.POST, request.FILES or None)
        if form.is_valid():
            if step < 5:
                _store_step(request, step, request.POST)
                if step == 1 and not _phone_verified(request):
                    return redirect("submissions:sell_verify")
                return redirect("submissions:sell_step", step=step + 1)
            return _finish_submission(request, form)
        messages.error(request, "Please correct the highlighted fields.")
    else:
        stored = _step_data(request, step)
        if stored is not None:
            form = form_class(stored)
        else:
            initial = {}
            if step == 1 and request.user.is_authenticated:
                initial = {
                    "owner_name": request.user.display_name,
                    "phone": request.user.phone,
                    "whatsapp": request.user.whatsapp,
                    "email": request.user.email,
                }
            if step == 2:
                initial = _wizard(request).get("prefill_2", {})
            form = form_class(initial=initial)

    property_type = _wizard_property_type(request)
    localities = Locality.objects.select_related("tehsil")
    context = {
        "form": form,
        "step": step,
        "step_title": title,
        "steps": [(n, STEPS[n][0]) for n in STEPS],
        "progress": int((step - 1) * 100 / 4),
        "is_agri": property_type in AGRICULTURAL_TYPES,
        "agri_types": list(AGRICULTURAL_TYPES),
        "type_icons": {str(k): v for k, v in PROPERTY_TYPE_ICONS.items()},
        "unit_factors": factors_for_js(),
        "locality_data": {
            str(loc.pk): {"tehsil": loc.tehsil_id, "lat": float(loc.latitude), "lng": float(loc.longitude), "name": loc.name}
            for loc in localities
        },
        "breadcrumbs": crumbs(("Sell Your Property", None)),
        "page_title": f"Sell Your Property in Agra - Step {step} of 5",
        "meta_description": "Submit your plot, land or farm in Agra for a free evaluation and a direct offer. No brokers.",
    }
    return render(request, "submissions/sell_step.html", context)


def sell_verify(request):
    """Mock OTP: shows the OTP on screen for the demo instead of sending an SMS."""
    step1 = _step_data(request, 1)
    if step1 is None:
        return redirect("submissions:sell_step", step=1)
    phone = step1.get("phone")
    if _phone_verified(request):
        return redirect("submissions:sell_step", step=2)

    if request.GET.get("resend") or "sell_otp" not in request.session:
        request.session["sell_otp"] = f"{random.randint(1000, 9999)}"
        messages.info(
            request, f"DEMO MODE: Your OTP is {request.session['sell_otp']}. In the live site this is sent by SMS."
        )

    form = OTPForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if form.cleaned_data["otp"] == request.session.get("sell_otp"):
            request.session["sell_verified_phone"] = phone
            request.session.pop("sell_otp", None)
            messages.success(request, "Mobile number verified.")
            return redirect("submissions:sell_step", step=2)
        form.add_error("otp", "Incorrect OTP. Please try again.")
    return render(
        request,
        "submissions/verify_otp.html",
        {"form": form, "phone": phone, "breadcrumbs": crumbs(("Sell Your Property", "/sell-your-property/"), ("Verify", None))},
    )


@transaction.atomic
def _finish_submission(request, final_form):
    wizard = _wizard(request)
    quick_id = wizard.get("quick_id")
    submission = None
    if quick_id:
        submission = PropertySubmission.objects.filter(pk=quick_id, is_complete=False).first()
    is_new = submission is None
    if is_new:
        submission = PropertySubmission()

    for step in range(1, 5):
        form = STEPS[step][1](_step_data(request, step), instance=submission)
        if not form.is_valid():
            messages.error(request, f"Please review step {step}: {STEPS[step][0]}.")
            return redirect("submissions:sell_step", step=step)
        submission = form.save(commit=False)
    submission = _apply_final(final_form, submission)

    if not submission.is_agricultural:
        for field in Step3SizeForm.AGRI_FIELDS:
            setattr(submission, field, False if field == "has_tubewell" else "")
    submission.whatsapp = submission.whatsapp or submission.phone
    submission.phone_verified = True
    submission.is_complete = True
    if request.user.is_authenticated and request.user.is_owner:
        submission.owner_user = request.user
    submission.save()

    for image in final_form.cleaned_data.get("photos", []):
        SubmissionPhoto.objects.create(submission=submission, image=image)
    doc_type = final_form.cleaned_data.get("document_type") or SubmissionDocument.DocType.OTHER
    for doc in final_form.cleaned_data.get("documents", []):
        SubmissionDocument.objects.create(submission=submission, file=doc, doc_type=doc_type)

    if is_new:
        StatusHistory.objects.create(submission=submission, new_status=Status.NEW, note="Submitted via website")
    log_activity(submission, request.user, "Full property details submitted", f"{submission.photos.count()} photos")

    request.session.pop(WIZARD_KEY, None)
    request.session["last_reference"] = submission.reference_id
    return redirect("submissions:thank_you", reference=submission.reference_id)


def _apply_final(form, submission):
    for name in form.Meta.fields:
        setattr(submission, name, form.cleaned_data.get(name))
    return submission


def thank_you(request, reference):
    submission = get_object_or_404(PropertySubmission, reference_id=reference)
    allowed = request.session.get("last_reference") == reference or (
        request.user.is_authenticated and (request.user.is_company_staff or submission.owner_user_id == request.user.pk)
    )
    if not allowed:
        raise Http404
    return render(
        request,
        "submissions/thank_you.html",
        {"submission": submission, "breadcrumbs": crumbs(("Sell Your Property", "/sell-your-property/"), ("Thank You", None))},
    )


# --------------------------------------------------------------------------
# Public tracking
# --------------------------------------------------------------------------
def build_timeline(submission):
    history = {h.new_status: h for h in submission.status_history.all()}
    current_index = submission.pipeline_index
    steps = []
    for index, status in enumerate(PIPELINE_ORDER):
        if submission.status in (Status.REJECTED, Status.WITHDREW):
            state = "done" if status in history else "skipped"
        elif index < current_index:
            state = "done"
        elif index == current_index:
            state = "current"
        else:
            state = "upcoming"
        entry = history.get(status)
        steps.append(
            {
                "label": status.label,
                "help": OWNER_STATUS_HELP[status],
                "state": state,
                "date": entry.timestamp if entry else None,
                "note": entry.note if entry else "",
            }
        )
    if submission.status in (Status.REJECTED, Status.WITHDREW):
        entry = history.get(submission.status)
        steps.append(
            {
                "label": Status(submission.status).label,
                "help": OWNER_STATUS_HELP[submission.status],
                "state": "closed",
                "date": entry.timestamp if entry else None,
                "note": entry.note if entry else "",
            }
        )
    return [s for s in steps if s["state"] != "skipped"]


def track(request):
    form = TrackForm(request.GET or None)
    submission = None
    if request.GET and form.is_valid():
        submission = PropertySubmission.objects.filter(
            reference_id=form.cleaned_data["reference_id"], phone=form.cleaned_data["phone"]
        ).first()
        if submission is None:
            form.add_error(None, "No submission found with this reference ID and mobile number.")
    return render(
        request,
        "submissions/track.html",
        {
            "form": form,
            "submission": submission,
            "timeline": build_timeline(submission) if submission else [],
            "demo_ref": PropertySubmission.objects.order_by("pk").first(),
            "breadcrumbs": crumbs(("Track Submission", None)),
        },
    )


# --------------------------------------------------------------------------
# Owner portal
# --------------------------------------------------------------------------
def owner_queryset(user):
    query = Q(owner_user=user)
    if user.phone:
        query |= Q(phone=user.phone)
    return PropertySubmission.objects.filter(query).select_related("locality")


@login_required
def owner_dashboard(request):
    if request.user.is_company_staff:
        return redirect("dashboard:overview")
    submissions = owner_queryset(request.user).prefetch_related("offers")
    open_offers = Offer.objects.filter(submission__in=submissions, status=Offer.OfferStatus.PENDING)
    return render(
        request,
        "submissions/owner/dashboard.html",
        {
            "submissions": submissions,
            "open_offers": open_offers,
            "active_count": submissions.exclude(status__in=CLOSED_STATUSES).count(),
            "acquired_count": submissions.filter(status=Status.ACQUIRED).count(),
        },
    )


@login_required
def owner_submission(request, reference):
    submission = get_object_or_404(owner_queryset(request.user), reference_id=reference)
    return render(
        request,
        "submissions/owner/submission_detail.html",
        {
            "submission": submission,
            "timeline": build_timeline(submission),
            "offers": submission.offers.all(),
            "next_visit": submission.site_visits.filter(status="scheduled").order_by("scheduled_for").first(),
            "upload_form": OwnerUploadForm(),
            "response_form": OfferResponseForm(),
        },
    )


@login_required
@require_POST
def owner_upload(request, reference):
    submission = get_object_or_404(owner_queryset(request.user), reference_id=reference)
    form = OwnerUploadForm(request.POST, request.FILES)
    if form.is_valid():
        for image in form.cleaned_data["photos"]:
            SubmissionPhoto.objects.create(submission=submission, image=image)
        doc_type = form.cleaned_data.get("document_type") or SubmissionDocument.DocType.OTHER
        for doc in form.cleaned_data["documents"]:
            SubmissionDocument.objects.create(submission=submission, file=doc, doc_type=doc_type)
        count = len(form.cleaned_data["photos"]) + len(form.cleaned_data["documents"])
        log_activity(submission, request.user, "Owner uploaded files", f"{count} file(s)")
        messages.success(request, f"{count} file(s) uploaded successfully.")
    else:
        for errors in form.errors.values():
            messages.error(request, errors[0])
    return redirect("submissions:owner_submission", reference=reference)


@login_required
@require_POST
def offer_respond(request, pk):
    offer = get_object_or_404(Offer.objects.select_related("submission"), pk=pk)
    submission = offer.submission
    if not owner_queryset(request.user).filter(pk=submission.pk).exists():
        raise Http404
    if not offer.is_open:
        messages.error(request, "This offer is no longer open for response.")
        return redirect("submissions:owner_submission", reference=submission.reference_id)

    form = OfferResponseForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Please enter a valid counter amount.")
        return redirect("submissions:owner_submission", reference=submission.reference_id)

    action, note = form.cleaned_data["action"], form.cleaned_data["note"]
    offer.owner_note = note
    offer.responded_at = timezone.now()
    if action == "accept":
        offer.status = Offer.OfferStatus.ACCEPTED
        offer.save()
        change_status(submission, Status.OFFER_ACCEPTED, request.user, "Owner accepted the offer online.")
        messages.success(request, "You accepted the offer. Our team will call you to plan the registry.")
    elif action == "reject":
        offer.status = Offer.OfferStatus.REJECTED
        offer.save()
        change_status(submission, Status.NEGOTIATION, request.user, "Owner rejected the offer.")
        messages.info(request, "Offer rejected. Our team may share a revised offer.")
    else:
        offer.status = Offer.OfferStatus.COUNTERED
        offer.owner_counter_amount = form.cleaned_data["counter_amount"]
        offer.save()
        change_status(submission, Status.NEGOTIATION, request.user, "Owner sent a counter offer.")
        messages.success(request, "Counter offer sent to our team.")
    log_activity(submission, request.user, f"Owner {action}ed offer", note)
    return redirect("submissions:owner_submission", reference=submission.reference_id)


@login_required
def notifications(request):
    items = request.user.notifications.all()[:50]
    response = render(request, "submissions/owner/notifications.html", {"items": items})
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return response


@login_required
def document_download(request, pk):
    """Documents are private: only company staff or the property's owner can open them."""
    document = get_object_or_404(SubmissionDocument.objects.select_related("submission"), pk=pk)
    user = request.user
    if not (user.is_company_staff or owner_queryset(user).filter(pk=document.submission_id).exists()):
        raise Http404
    return FileResponse(document.file.open("rb"), filename=document.filename)
