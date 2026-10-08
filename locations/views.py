from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from core.seo import crumbs, faq_schema
from core.templatetags.site_tags import inr, inr_short
from listings.models import Listing
from submissions.constants import AGRICULTURAL_TYPES, CircleCategory, PropertyType
from submissions.forms import QuickLeadForm

from .forms import EstimatorForm
from .models import Locality, Tehsil
from .services import estimate_price
from .units import factors_for_js


class SimpleFAQ:
    def __init__(self, question, answer):
        self.question, self.answer = question, answer


def area_index(request):
    tehsils = Tehsil.objects.prefetch_related("localities")
    return render(
        request,
        "locations/area_index.html",
        {"tehsils": tehsils, "breadcrumbs": crumbs(("Sell Land in Agra", None))},
    )


def locality_detail(request, slug):
    locality = get_object_or_404(Locality.objects.select_related("tehsil"), slug=slug)
    faqs = list(locality.faqs.all())
    rates = locality.circle_rates.all()
    listings = Listing.objects.filter(locality=locality).exclude(status=Listing.ListingStatus.SOLD)[:6]
    nearby = Locality.objects.filter(tehsil=locality.tehsil).exclude(pk=locality.pk)[:6]
    context = {
        "locality": locality,
        "faqs": faqs,
        "rates": rates,
        "listings": listings,
        "nearby": nearby,
        "quick_form": QuickLeadForm(initial={"locality": locality.pk}),
        "breadcrumbs": crumbs(("Sell Land in Agra", "/sell-land-in-agra/"), (locality.name, None)),
        "schemas": [faq_schema(faqs)] if faqs else [],
    }
    return render(request, "locations/locality_detail.html", context)


TYPE_LANDINGS = {
    "plot": {
        "h1": "Sell Your Plot in Agra Directly",
        "hero_image": "img/photos/plot-01.jpg",
        "title": "Sell Plot in Agra | Get Fair Price in 7 Days, No Broker",
        "description": "Sell residential plots in Agra colonies like Kamla Nagar, Shastripuram, Sikandra and Fatehabad Road directly to BhoomiDirect. Free valuation, fast payment.",
        "types": [PropertyType.RESIDENTIAL_PLOT, PropertyType.OLD_CONSTRUCTION],
        "category": CircleCategory.RESIDENTIAL,
        "intro": "Own a residential plot in an Agra colony, ADA layout or a plot with an old house on it? We buy plots directly, verify papers with our own legal team, and pay at registry. No brokerage, no endless buyer visits.",
        "points": [
            "Plots from 50 gaj to 2000 gaj considered",
            "Old construction? We value it as plot + structure",
            "ADA approved and unapproved colonies both evaluated",
            "Offer usually within 7 days of site visit",
        ],
        "faqs": [
            ("Do you buy plots in unapproved colonies?", "Yes. We evaluate every plot. Unapproved colony plots are priced after checking registry, mutation and road access."),
            ("How is the price of my plot decided?", "We look at locality demand, road width, facing, corner position, circle rate and recent deals nearby."),
            ("Can I sell a plot that has an old house?", "Yes. Choose 'Plot with Old Construction' in the form. We value the land and the structure separately."),
        ],
    },
    "agricultural": {
        "h1": "Sell Agricultural Land in Agra",
        "hero_image": "img/photos/agri-01.jpg",
        "title": "Sell Agricultural Land in Agra | Khet, Farm & Bigha Land Buyers",
        "description": "Sell agricultural land in Agra, Etmadpur, Kiraoli, Fatehabad, Bah and Kheragarh tehsils directly. Khatauni check, fair price per bigha and fast payment.",
        "types": list(AGRICULTURAL_TYPES),
        "category": CircleCategory.AGRICULTURAL,
        "intro": "We buy agricultural land (khet) and farmhouse land across all tehsils of Agra district. Tell us the bigha size, khasra number and irrigation details, and our team will check the Khatauni and visit the land.",
        "points": [
            "Land from 1 bigha to 50+ bigha",
            "Expressway and highway belt land preferred",
            "Joint family land (multiple khatedars) handled",
            "We help with mutation and paperwork",
        ],
        "faqs": [
            ("What size of bigha do you use in Agra?", "We use the pucca bigha common in Agra (approx. 27,225 sq ft). Our form converts any unit automatically."),
            ("My land has 4 co-owners in Khatauni. Can I still sell?", "Yes, all co-owners must agree and sign at registry. We guide the family through the process."),
            ("Do you buy land without road access?", "We do evaluate it, but land with a pucca road or rasta in records gets a better price."),
        ],
    },
    "commercial": {
        "h1": "Sell Commercial & Industrial Land in Agra",
        "hero_image": "img/photos/road-06.jpg",
        "title": "Sell Commercial Land in Agra | Highway & Industrial Plot Buyers",
        "description": "Sell commercial plots, highway-facing land and industrial land in Agra on Gwalior Road, Fatehabad Road, Sikandra and Runkata directly to us.",
        "types": [PropertyType.COMMERCIAL_PLOT, PropertyType.INDUSTRIAL_LAND],
        "category": CircleCategory.COMMERCIAL,
        "intro": "Highway frontage, market-facing plots and industrial land get special attention from our evaluation team. We buy for long-term resale to businesses and developers in our network.",
        "points": [
            "Highway and main road frontage land",
            "Industrial land near Sikandra and Runkata",
            "Quick legal due diligence",
            "Bulk deals with transparent valuation",
        ],
        "faqs": [
            ("Do you buy land that needs change of land use (CLU)?", "Yes, we factor CLU cost and time into our offer."),
            ("Is frontage important for commercial land?", "Yes. Frontage and road width are two of the biggest price drivers for commercial land."),
            ("How fast can you close a commercial deal?", "Once legal is clear, most deals close in 2 to 4 weeks."),
        ],
    },
}


def type_landing(request, kind):
    config = TYPE_LANDINGS[kind]
    faqs = [SimpleFAQ(q, a) for q, a in config["faqs"]]
    localities = Locality.objects.filter(circle_rates__property_type=config["category"]).distinct()
    context = {
        "config": config,
        "faqs": faqs,
        "page_title": config["title"],
        "meta_description": config["description"],
        "localities": localities,
        "listings": Listing.objects.filter(property_type__in=config["types"]).exclude(
            status=Listing.ListingStatus.SOLD
        )[:3],
        "quick_form": QuickLeadForm(initial={"property_type": config["types"][0]}),
        "breadcrumbs": crumbs((config["h1"], None)),
        "schemas": [faq_schema(faqs)],
    }
    return render(request, "locations/type_landing.html", context)


def estimator(request):
    submitted = "area_value" in request.GET
    form = EstimatorForm(request.GET if submitted else None, initial=request.GET.dict())
    result = None
    if submitted and form.is_valid():
        data = form.cleaned_data
        result = estimate_price(data["locality"], data["property_type"], data["area_value"], data["area_unit"])
        if result is None:
            form.add_error(None, "No sample rate is available for this area and type yet. Submit your property for an exact offer.")
    return render(
        request,
        "locations/estimator.html",
        {
            "form": form,
            "result": result,
            "unit_factors": factors_for_js(),
            "breadcrumbs": crumbs(("Instant Price Estimate", None)),
            "low_mult": settings.ESTIMATOR_MARKET_MULTIPLIER_LOW,
            "high_mult": settings.ESTIMATOR_MARKET_MULTIPLIER_HIGH,
        },
    )


@require_GET
def estimator_api(request):
    form = EstimatorForm(request.GET)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)
    data = form.cleaned_data
    result = estimate_price(data["locality"], data["property_type"], data["area_value"], data["area_unit"])
    if result is None:
        return JsonResponse({"ok": False, "message": "No sample rate available for this combination."})
    return JsonResponse(
        {
            "ok": True,
            "low": inr_short(result["low"]),
            "high": inr_short(result["high"]),
            "circle_value": inr(result["circle_value"]),
            "rate": inr(result["rate_per_sq_meter"]),
            "sq_meter": float(result["sq_meter"]),
            "year": result["rate_year"],
        }
    )
