from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from core.seo import absolute, crumbs

from .forms import InquiryForm, ListingFilterForm
from .models import Listing

PAGE_SIZE = 6


def listing_list(request):
    form = ListingFilterForm(request.GET or None)
    queryset = form.filter(Listing.objects.select_related("locality").prefetch_related("photos"))
    page = Paginator(queryset, PAGE_SIZE).get_page(request.GET.get("page"))
    context = {"form": form, "page_obj": page, "total": queryset.count()}

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string("listings/_results.html", context, request=request)
        return JsonResponse({"html": html, "total": context["total"]})

    context.update(
        {
            "breadcrumbs": crumbs(("Buy Property in Agra", None)),
            "page_title": "Buy Plots & Land in Agra | Verified, Clear Title Properties",
            "meta_description": "Buy legally verified plots, agricultural land and commercial land in Agra directly from BhoomiDirect. Clear title, no broker hassle.",
        }
    )
    return render(request, "listings/list.html", context)


def listing_schema(listing, request):
    data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": listing.title,
        "description": listing.seo_description,
        "url": absolute(listing.get_absolute_url()),
        "category": listing.get_property_type_display(),
        "offers": {
            "@type": "Offer",
            "price": str(int(listing.price)),
            "priceCurrency": "INR",
            "availability": "https://schema.org/InStock"
            if listing.status == Listing.ListingStatus.AVAILABLE
            else "https://schema.org/SoldOut",
            "areaServed": listing.locality.name,
        },
    }
    if listing.cover:
        data["image"] = request.build_absolute_uri(listing.cover.image.url)
    return data


def listing_detail(request, slug):
    listing = get_object_or_404(Listing.objects.select_related("locality", "locality__tehsil"), slug=slug)
    similar = (
        Listing.objects.filter(property_type=listing.property_type)
        .exclude(pk=listing.pk)
        .exclude(status=Listing.ListingStatus.SOLD)[:3]
    )
    context = {
        "listing": listing,
        "photos": listing.photos.all(),
        "similar": similar,
        "form": InquiryForm(),
        "breadcrumbs": crumbs(("Buy Property", "/buy-property-in-agra/"), (listing.title, None)),
        "schemas": [listing_schema(listing, request)],
    }
    return render(request, "listings/detail.html", context)


@require_POST
def listing_inquiry(request, slug):
    listing = get_object_or_404(Listing, slug=slug)
    form = InquiryForm(request.POST)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    if form.is_valid():
        inquiry = form.save(commit=False)
        inquiry.listing = listing
        user = request.user
        if user.is_authenticated and user.is_partner and hasattr(user, "partner_profile"):
            inquiry.referred_by = user.partner_profile
        inquiry.save()
        msg = "Thank you! Our sales team will call you shortly."
        if is_ajax:
            return JsonResponse({"ok": True, "message": msg})
        messages.success(request, msg)
        return redirect(listing.get_absolute_url())
    if is_ajax:
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)
    messages.error(request, "Please check the inquiry form.")
    return redirect(listing.get_absolute_url())
