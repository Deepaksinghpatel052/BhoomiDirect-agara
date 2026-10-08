"""Company staff dashboard (/dashboard/)."""
import csv
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import role_required, staff_required
from accounts.models import User
from core.templatetags.site_tags import inr_short
from listings.forms import ListingEditForm
from listings.models import BuyerInquiry, Listing, ListingPhoto
from locations.forms import CircleRateForm, LocalityForm
from locations.models import CircleRate, Locality
from partners.models import ChannelPartner
from submissions.constants import PIPELINE_ORDER, PropertyType, Status
from submissions.models import PropertySubmission, StatusHistory
from submissions.services import change_status, log_activity, notify_owner

from .forms import (
    AcquisitionForm,
    AssignAgentForm,
    EvaluationForm,
    LeadFilterForm,
    LegalChecklistForm,
    NoteForm,
    OfferForm,
    SiteVisitForm,
    SiteVisitReportForm,
    StatusForm,
)
from .models import Acquisition, ActivityLog, Evaluation, InternalNote, LegalChecklist, Offer, SiteVisit, SiteVisitPhoto

R = User.Role
DECISION_ROLES = (R.ADMIN, R.EVALUATOR)


def _lead_qs():
    return PropertySubmission.objects.select_related("locality", "assigned_agent", "tehsil")


def _back(pk):
    return redirect("dashboard:lead_detail", pk=pk)


def _form_errors(request, form):
    for field, errors in form.errors.items():
        label = form.fields[field].label if field in form.fields else ""
        messages.error(request, f"{label}: {errors[0]}" if label else errors[0])


# --------------------------------------------------------------------------
# Overview
# --------------------------------------------------------------------------
@staff_required
def overview(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)
    subs = PropertySubmission.objects.all()
    open_listings = Listing.objects.exclude(status=Listing.ListingStatus.SOLD)

    kpis = {
        "new_today": subs.filter(created_at__date=today).count(),
        "new_week": subs.filter(created_at__date__gte=today - timedelta(days=7)).count(),
        "under_evaluation": subs.filter(status__in=[Status.UNDER_EVALUATION, Status.LEGAL_VERIFICATION]).count(),
        "offers_pending": Offer.objects.filter(status=Offer.OfferStatus.PENDING).count(),
        "acquired_month": Acquisition.objects.filter(purchase_date__gte=month_start).count(),
        "acquired_total": Acquisition.objects.count(),
        "inventory_value": open_listings.aggregate(v=Sum("price"))["v"] or 0,
        "inventory_count": open_listings.count(),
        "sold": Listing.objects.filter(status=Listing.ListingStatus.SOLD).count(),
        "total_leads": subs.count(),
    }

    # Leads per week (last 8 weeks)
    week_labels, week_counts = [], []
    start = today - timedelta(days=today.weekday()) - timedelta(weeks=7)
    for i in range(8):
        w_start = start + timedelta(weeks=i)
        w_end = w_start + timedelta(days=7)
        week_labels.append(w_start.strftime("%d %b"))
        week_counts.append(subs.filter(created_at__date__gte=w_start, created_at__date__lt=w_end).count())

    by_locality = list(
        subs.exclude(locality=None).values("locality__name").annotate(n=Count("id")).order_by("-n")[:8]
    )
    type_labels = dict(PropertyType.choices)
    by_type = list(subs.values("property_type").annotate(n=Count("id")).order_by("-n"))

    # Funnel: how many leads ever reached each stage (from status history).
    reached = []
    for i, status in enumerate(PIPELINE_ORDER):
        later = PIPELINE_ORDER[i:]
        reached.append(
            StatusHistory.objects.filter(new_status__in=later).values("submission").distinct().count()
        )

    charts = {
        "weeks": {"labels": week_labels, "data": week_counts},
        "locality": {"labels": [r["locality__name"] for r in by_locality], "data": [r["n"] for r in by_locality]},
        "type": {"labels": [type_labels[r["property_type"]] for r in by_type], "data": [r["n"] for r in by_type]},
        "funnel": {"labels": [s.label for s in PIPELINE_ORDER], "data": reached},
    }
    return render(
        request,
        "dashboard/overview.html",
        {
            "kpis": kpis,
            "charts": charts,
            "recent_leads": _lead_qs()[:8],
            "upcoming_visits": SiteVisit.objects.filter(status="scheduled", scheduled_for__gte=timezone.now())
            .select_related("submission", "agent")
            .order_by("scheduled_for")[:6],
            "recent_activity": ActivityLog.objects.select_related("user", "submission")[:10],
            "nav": "overview",
        },
    )


# --------------------------------------------------------------------------
# Leads table / CSV / Kanban
# --------------------------------------------------------------------------
@staff_required
def leads(request):
    form = LeadFilterForm(request.GET or None)
    qs = form.filter(_lead_qs())
    page = Paginator(qs, 20).get_page(request.GET.get("page"))
    return render(
        request, "dashboard/leads.html", {"form": form, "page_obj": page, "total": qs.count(), "nav": "leads"}
    )


@role_required(R.ADMIN, R.EVALUATOR)
def leads_export(request):
    form = LeadFilterForm(request.GET or None)
    qs = form.filter(_lead_qs())
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="leads-{timezone.localdate()}.csv"'
    response.write("﻿")  # BOM so Excel shows ₹ and Hindi correctly
    writer = csv.writer(response)
    writer.writerow(
        ["Reference", "Owner", "Phone", "Type", "Tehsil", "Locality", "Area", "Area (sq m)", "Expected price",
         "Urgency", "Status", "Source", "Agent", "Created"]
    )
    for s in qs:
        writer.writerow(
            [s.reference_id, s.owner_name, s.phone, s.get_property_type_display(), s.tehsil or "", s.locality or "",
             s.area_display, s.area_sq_meter or "", s.expected_price or "", s.get_urgency_display(),
             s.get_status_display(), s.get_source_display(), s.assigned_agent or "", s.created_at.strftime("%Y-%m-%d")]
        )
    return response


@staff_required
def pipeline(request):
    columns = []
    qs = _lead_qs().prefetch_related("photos")
    agent_only = request.GET.get("mine") == "1"
    if agent_only:
        qs = qs.filter(assigned_agent=request.user)
    for status in Status:
        columns.append({"status": status, "items": [s for s in qs if s.status == status]})
    return render(request, "dashboard/pipeline.html", {"columns": columns, "nav": "pipeline", "mine": agent_only})


@staff_required
@require_POST
def pipeline_move(request):
    submission = get_object_or_404(PropertySubmission, pk=request.POST.get("pk"))
    new_status = request.POST.get("status")
    if new_status not in Status.values:
        return JsonResponse({"ok": False, "message": "Unknown status"}, status=400)
    if new_status == Status.ACQUIRED and not hasattr(submission, "acquisition"):
        return JsonResponse(
            {"ok": False, "message": "Use 'Mark as Acquired' on the lead page to record purchase details."}, status=400
        )
    if new_status in (Status.OFFER_MADE,) and not request.user.has_any_role(*DECISION_ROLES):
        return JsonResponse({"ok": False, "message": "Only evaluators/admin can move leads to Offer Made."}, status=403)
    change_status(submission, new_status, request.user, "Moved on pipeline board")
    return JsonResponse({"ok": True, "message": f"{submission.reference_id} moved to {Status(new_status).label}"})


# --------------------------------------------------------------------------
# Lead detail and actions
# --------------------------------------------------------------------------
@staff_required
def lead_detail(request, pk):
    submission = get_object_or_404(_lead_qs(), pk=pk)
    evaluation = getattr(submission, "evaluation", None)
    checklist, _ = LegalChecklist.objects.get_or_create(submission=submission)
    context = {
        "s": submission,
        "evaluation": evaluation,
        "checklist": checklist,
        "visits": submission.site_visits.select_related("agent").prefetch_related("photos"),
        "offers": submission.offers.select_related("created_by"),
        "activities": submission.activities.select_related("user")[:30],
        "notes": submission.internal_notes.select_related("author"),
        "history": submission.status_history.select_related("changed_by"),
        "acquisition": getattr(submission, "acquisition", None),
        "assign_form": AssignAgentForm(initial={"agent": submission.assigned_agent_id}),
        "status_form": StatusForm(initial={"status": submission.status}),
        "visit_form": SiteVisitForm(initial={"agent": submission.assigned_agent_id}),
        "evaluation_form": EvaluationForm(instance=evaluation),
        "legal_form": LegalChecklistForm(instance=checklist),
        "offer_form": OfferForm(initial={"amount": submission.expected_price}),
        "acquisition_form": AcquisitionForm(initial=_acquisition_initial(submission)),
        "note_form": NoteForm(),
        "can_decide": request.user.has_any_role(*DECISION_ROLES),
        "is_admin": request.user.is_admin_role,
        "nav": "leads",
    }
    return render(request, "dashboard/lead_detail.html", context)


def _acquisition_initial(submission):
    accepted = submission.offers.filter(status=Offer.OfferStatus.ACCEPTED).first()
    price = accepted.amount if accepted else submission.expected_price
    if not price:
        return {}
    # UP stamp duty ~7% (demo assumption), registration fee 1%.
    return {"purchase_price": price, "stamp_duty": round(price * 7 / 100), "registration_fee": round(price / 100)}


@staff_required
@require_POST
def lead_assign(request, pk):
    submission = get_object_or_404(PropertySubmission, pk=pk)
    form = AssignAgentForm(request.POST)
    if form.is_valid():
        submission.assigned_agent = form.cleaned_data["agent"]
        submission.save(update_fields=["assigned_agent", "updated_at"])
        log_activity(submission, request.user, "Agent assigned", str(submission.assigned_agent or "Unassigned"))
        messages.success(request, "Agent assignment updated.")
    return _back(pk)


@staff_required
@require_POST
def lead_status(request, pk):
    submission = get_object_or_404(PropertySubmission, pk=pk)
    form = StatusForm(request.POST)
    if form.is_valid():
        changed = change_status(submission, form.cleaned_data["status"], request.user, form.cleaned_data["note"])
        messages.success(request, "Status updated." if changed else "Status unchanged.")
    else:
        _form_errors(request, form)
    return _back(pk)


@staff_required
@require_POST
def lead_note(request, pk):
    submission = get_object_or_404(PropertySubmission, pk=pk)
    form = NoteForm(request.POST)
    if form.is_valid():
        InternalNote.objects.create(submission=submission, author=request.user, text=form.cleaned_data["text"])
        log_activity(submission, request.user, "Internal note added")
        messages.success(request, "Note added.")
    return _back(pk)


@staff_required
@require_POST
def visit_create(request, pk):
    submission = get_object_or_404(PropertySubmission, pk=pk)
    form = SiteVisitForm(request.POST)
    if form.is_valid():
        visit = form.save(commit=False)
        visit.submission = submission
        visit.save()
        if not submission.assigned_agent_id:
            submission.assigned_agent = visit.agent
            submission.save(update_fields=["assigned_agent", "updated_at"])
        when = timezone.localtime(visit.scheduled_for).strftime("%d %b %Y, %I:%M %p")
        change_status(submission, Status.VISIT_SCHEDULED, request.user, f"Site visit on {when} by {visit.agent}")
        messages.success(request, "Site visit scheduled.")
    else:
        _form_errors(request, form)
    return _back(pk)


@staff_required
def visit_report(request, visit_pk):
    visit = get_object_or_404(SiteVisit.objects.select_related("submission", "agent"), pk=visit_pk)
    if request.user.role == R.FIELD_AGENT and visit.agent_id != request.user.pk:
        messages.error(request, "This visit is assigned to another agent.")
        return redirect("dashboard:site_visits")
    form = SiteVisitReportForm(request.POST or None, request.FILES or None, instance=visit)
    if request.method == "POST" and form.is_valid():
        visit = form.save()
        for image in form.cleaned_data.get("photos", []):
            SiteVisitPhoto.objects.create(visit=visit, image=image)
        log_activity(visit.submission, request.user, "Site visit report updated", visit.get_status_display())
        if visit.status == SiteVisit.VisitStatus.COMPLETED:
            change_status(visit.submission, Status.VISIT_DONE, request.user, "Site visit completed")
        messages.success(request, "Visit report saved.")
        return redirect("dashboard:lead_detail", pk=visit.submission_id)
    return render(request, "dashboard/visit_report.html", {"visit": visit, "form": form, "nav": "visits"})


@role_required(*DECISION_ROLES)
@require_POST
def evaluation_save(request, pk):
    submission = get_object_or_404(PropertySubmission, pk=pk)
    instance = getattr(submission, "evaluation", None) or Evaluation(submission=submission)
    form = EvaluationForm(request.POST, instance=instance)
    if form.is_valid():
        evaluation = form.save(commit=False)
        evaluation.evaluator = request.user
        evaluation.save()
        log_activity(
            submission, request.user, "Evaluation saved",
            f"Score {evaluation.total_score}/60 - {evaluation.get_recommendation_display()}",
        )
        if submission.status in (Status.NEW, Status.CONTACTED, Status.VISIT_SCHEDULED, Status.VISIT_DONE):
            change_status(submission, Status.UNDER_EVALUATION, request.user, "Evaluation started")
        messages.success(request, f"Evaluation saved: {evaluation.get_recommendation_display()}.")
    else:
        _form_errors(request, form)
    return _back(pk)


@role_required(*DECISION_ROLES)
@require_POST
def legal_save(request, pk):
    submission = get_object_or_404(PropertySubmission, pk=pk)
    checklist, _ = LegalChecklist.objects.get_or_create(submission=submission)
    form = LegalChecklistForm(request.POST, instance=checklist)
    if form.is_valid():
        checklist = form.save(commit=False)
        checklist.verified_by = request.user
        checklist.save()
        log_activity(submission, request.user, "Legal checklist updated", f"{checklist.progress}% complete")
        if submission.status == Status.UNDER_EVALUATION:
            change_status(submission, Status.LEGAL_VERIFICATION, request.user, "Legal verification in progress")
        messages.success(request, f"Legal checklist saved ({checklist.progress}% complete).")
    return _back(pk)


@role_required(*DECISION_ROLES)
@require_POST
def offer_create(request, pk):
    submission = get_object_or_404(PropertySubmission, pk=pk)
    form = OfferForm(request.POST)
    if form.is_valid():
        offer = form.save(commit=False)
        offer.submission = submission
        offer.created_by = request.user
        offer.save()
        submission.offers.filter(status=Offer.OfferStatus.PENDING).exclude(pk=offer.pk).update(
            status=Offer.OfferStatus.REJECTED
        )
        changed = change_status(
            submission, Status.OFFER_MADE, request.user, f"Offer of {inr_short(offer.amount)} made. Please respond."
        )
        if not changed:
            notify_owner(submission, "Revised offer received", f"New offer: {inr_short(offer.amount)}. Please respond.")
        messages.success(request, "Offer created and owner notified.")
    else:
        _form_errors(request, form)
    return _back(pk)


@role_required(*DECISION_ROLES)
@require_POST
def offer_staff_update(request, offer_pk):
    """Staff records an owner's response received over phone/WhatsApp."""
    offer = get_object_or_404(Offer.objects.select_related("submission"), pk=offer_pk)
    action = request.POST.get("action")
    if action == "accept":
        offer.status = Offer.OfferStatus.ACCEPTED
        change_status(offer.submission, Status.OFFER_ACCEPTED, request.user, "Owner accepted (recorded by staff)")
    elif action == "reject":
        offer.status = Offer.OfferStatus.REJECTED
        change_status(offer.submission, Status.NEGOTIATION, request.user, "Offer rejected (recorded by staff)")
    else:
        messages.error(request, "Unknown action.")
        return _back(offer.submission_id)
    offer.responded_at = timezone.now()
    offer.save()
    log_activity(offer.submission, request.user, f"Offer marked {offer.get_status_display()}")
    messages.success(request, f"Offer marked {offer.get_status_display()}.")
    return _back(offer.submission_id)


@role_required(R.ADMIN)
@require_POST
@transaction.atomic
def acquire(request, pk):
    submission = get_object_or_404(PropertySubmission, pk=pk)
    if hasattr(submission, "acquisition"):
        messages.info(request, "This property is already acquired.")
        return _back(pk)
    form = AcquisitionForm(request.POST)
    if form.is_valid():
        acquisition = form.save(commit=False)
        acquisition.submission = submission
        acquisition.created_by = request.user
        acquisition.save()
        change_status(submission, Status.ACQUIRED, request.user, "Registry done, payment released")
        messages.success(request, "Marked as acquired. You can now publish it for resale.")
    else:
        _form_errors(request, form)
    return _back(pk)


# --------------------------------------------------------------------------
# Site visits
# --------------------------------------------------------------------------
@staff_required
def site_visits(request):
    visits = SiteVisit.objects.select_related("submission__locality", "agent")
    if request.user.role == R.FIELD_AGENT:
        visits = visits.filter(agent=request.user)
    show = request.GET.get("show", "upcoming")
    if show == "upcoming":
        visits = visits.filter(status=SiteVisit.VisitStatus.SCHEDULED).order_by("scheduled_for")
    elif show == "done":
        visits = visits.filter(status=SiteVisit.VisitStatus.COMPLETED)
    days = {}
    for visit in visits:
        days.setdefault(timezone.localtime(visit.scheduled_for).date(), []).append(visit)
    return render(request, "dashboard/site_visits.html", {"days": days, "show": show, "nav": "visits"})


# --------------------------------------------------------------------------
# Acquired properties, inventory, inquiries
# --------------------------------------------------------------------------
@staff_required
def acquisitions_list(request):
    items = Acquisition.objects.select_related("submission__locality", "listing")
    ready = PropertySubmission.objects.filter(status=Status.OFFER_ACCEPTED).select_related("locality")
    return render(
        request,
        "dashboard/acquisitions.html",
        {"items": items, "ready": ready, "total_cost": items.aggregate(v=Sum("total_cost"))["v"] or 0, "nav": "acquired"},
    )


@role_required(R.ADMIN)
@require_POST
def publish_listing(request, acquisition_pk):
    acquisition = get_object_or_404(Acquisition.objects.select_related("submission__locality"), pk=acquisition_pk)
    if hasattr(acquisition, "listing"):
        messages.info(request, "Already published.")
        return redirect("dashboard:inventory")
    listing = create_listing_from_acquisition(acquisition)
    log_activity(acquisition.submission, request.user, "Published for resale", listing.title)
    messages.success(request, f"Published '{listing.title}' for resale.")
    return redirect("dashboard:listing_edit", pk=listing.pk)


def create_listing_from_acquisition(acquisition, markup=1.25):
    """One-click resale listing. Price = total cost + 25% (editable afterwards)."""
    s = acquisition.submission
    features = []
    if s.road_width_ft:
        features.append(f"{s.road_width_ft} ft wide road")
    if s.is_corner:
        features.append("Corner plot")
    if s.has_boundary_wall:
        features.append("Boundary wall done")
    if s.has_electricity:
        features.append("Electricity connection available")
    if s.irrigation_source and s.irrigation_source != "none":
        features.append(f"Irrigation: {s.get_irrigation_source_display()}")
    features += ["Clear title, verified by our legal team", "Registry in your name directly", "No brokerage"]
    listing = Listing.objects.create(
        acquisition=acquisition,
        title=f"{s.area_display} {s.get_property_type_display()} in {s.locality.name if s.locality else 'Agra'}",
        description=(
            f"Legally verified {s.get_property_type_display().lower()} of {s.area_display} in "
            f"{s.locality.name if s.locality else 'Agra'}"
            f"{', ' + s.village_colony if s.village_colony else ''}. "
            f"{'Facing ' + s.get_facing_display() + '. ' if s.facing else ''}"
            "Owned by BhoomiDirect Agra with complete documentation, ready for immediate registry."
        ),
        price=round(acquisition.total_cost * Decimal(str(markup)), -4),
        area_value=s.area_value or 0,
        area_unit=s.area_unit,
        property_type=s.property_type,
        locality=s.locality,
        latitude=s.latitude or (s.locality.latitude if s.locality else None),
        longitude=s.longitude or (s.locality.longitude if s.locality else None),
        features="\n".join(features),
        road_width_ft=s.road_width_ft,
        facing=s.get_facing_display() if s.facing else "",
    )
    for i, photo in enumerate(s.photos.all()):
        ListingPhoto.objects.create(listing=listing, image=photo.image.name, alt_text=f"{listing.title} photo {i + 1}", order=i)
    return listing


@staff_required
def inventory(request):
    listings = Listing.objects.select_related("locality", "acquisition").annotate(n_inquiries=Count("inquiries"))
    status = request.GET.get("status")
    if status:
        listings = listings.filter(status=status)
    sold = Listing.objects.filter(status=Listing.ListingStatus.SOLD).select_related("acquisition")
    total_profit = sum((l.profit or 0) for l in sold)
    return render(
        request,
        "dashboard/inventory.html",
        {"listings": listings, "status": status, "total_profit": total_profit, "statuses": Listing.ListingStatus.choices, "nav": "inventory"},
    )


@role_required(R.ADMIN)
def listing_edit(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    form = ListingEditForm(request.POST or None, instance=listing)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Listing updated.")
        return redirect("dashboard:inventory")
    return render(request, "dashboard/listing_edit.html", {"form": form, "listing": listing, "nav": "inventory"})


@role_required(R.ADMIN)
@require_POST
def listing_status(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    status = request.POST.get("status")
    if status not in Listing.ListingStatus.values:
        messages.error(request, "Invalid status.")
        return redirect("dashboard:inventory")
    listing.status = status
    if status == Listing.ListingStatus.SOLD:
        try:
            listing.sold_price = int(request.POST.get("sold_price") or listing.price)
        except ValueError:
            listing.sold_price = listing.price
        listing.sold_date = timezone.localdate()
    listing.save()
    messages.success(request, f"'{listing.title}' marked {listing.get_status_display()}.")
    return redirect("dashboard:inventory")


@staff_required
def inquiries(request):
    items = BuyerInquiry.objects.select_related("listing", "referred_by")
    status = request.GET.get("status")
    if status:
        items = items.filter(status=status)
    return render(
        request,
        "dashboard/inquiries.html",
        {"items": items, "status": status, "statuses": BuyerInquiry.InquiryStatus.choices, "nav": "inquiries"},
    )


@staff_required
@require_POST
def inquiry_status(request, pk):
    inquiry = get_object_or_404(BuyerInquiry, pk=pk)
    status = request.POST.get("status")
    if status in BuyerInquiry.InquiryStatus.values:
        inquiry.status = status
        inquiry.save(update_fields=["status"])
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": True, "message": f"Inquiry from {inquiry.name} updated"})
        messages.success(request, "Inquiry updated.")
    return redirect("dashboard:inquiries")


# --------------------------------------------------------------------------
# Partners
# --------------------------------------------------------------------------
@staff_required
def partners(request):
    items = ChannelPartner.objects.prefetch_related("areas_covered").annotate(
        n_owner=Count("owner_referrals", distinct=True), n_buyer=Count("buyer_referrals", distinct=True)
    )
    return render(request, "dashboard/partners.html", {"items": items, "nav": "partners"})


@role_required(R.ADMIN)
@require_POST
def partner_toggle(request, pk):
    partner = get_object_or_404(ChannelPartner, pk=pk)
    partner.is_approved = not partner.is_approved
    partner.save(update_fields=["is_approved"])
    messages.success(request, f"{partner.name} {'approved' if partner.is_approved else 'set to pending'}.")
    return redirect("dashboard:partners")


# --------------------------------------------------------------------------
# Localities & circle rates
# --------------------------------------------------------------------------
@staff_required
def locations_manage(request):
    localities = Locality.objects.select_related("tehsil").annotate(n_leads=Count("submissions"))
    rates = CircleRate.objects.select_related("locality")
    return render(
        request,
        "dashboard/locations.html",
        {"localities": localities, "rates": rates, "rate_form": CircleRateForm(), "nav": "locations"},
    )


@role_required(R.ADMIN)
def locality_edit(request, pk=None):
    locality = get_object_or_404(Locality, pk=pk) if pk else None
    form = LocalityForm(request.POST or None, instance=locality)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Locality saved.")
        return redirect("dashboard:locations")
    return render(request, "dashboard/locality_edit.html", {"form": form, "locality": locality, "nav": "locations"})


@role_required(R.ADMIN)
def circle_rate_edit(request, pk=None):
    rate = get_object_or_404(CircleRate, pk=pk) if pk else None
    form = CircleRateForm(request.POST or None, instance=rate)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Sample circle rate saved.")
            return redirect("dashboard:locations")
        if not pk:
            _form_errors(request, form)
            return redirect("dashboard:locations")
    return render(request, "dashboard/circle_rate_edit.html", {"form": form, "rate": rate, "nav": "locations"})
