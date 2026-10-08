"""Shared choices used across submissions, acquisitions, listings and locations."""
from django.db import models


class PropertyType(models.TextChoices):
    RESIDENTIAL_PLOT = "residential_plot", "Residential Plot"
    COMMERCIAL_PLOT = "commercial_plot", "Commercial Plot"
    AGRICULTURAL_LAND = "agricultural_land", "Agricultural Land"
    FARMHOUSE_LAND = "farmhouse_land", "Farmhouse Land"
    INDUSTRIAL_LAND = "industrial_land", "Industrial Land"
    OLD_CONSTRUCTION = "old_construction", "Plot with Old Construction"


AGRICULTURAL_TYPES = (PropertyType.AGRICULTURAL_LAND, PropertyType.FARMHOUSE_LAND)

PROPERTY_TYPE_ICONS = {
    PropertyType.RESIDENTIAL_PLOT: "bi-house-door",
    PropertyType.COMMERCIAL_PLOT: "bi-shop",
    PropertyType.AGRICULTURAL_LAND: "bi-flower1",
    PropertyType.FARMHOUSE_LAND: "bi-tree",
    PropertyType.INDUSTRIAL_LAND: "bi-buildings",
    PropertyType.OLD_CONSTRUCTION: "bi-house-gear",
}


class CircleCategory(models.TextChoices):
    RESIDENTIAL = "residential", "Residential"
    COMMERCIAL = "commercial", "Commercial"
    AGRICULTURAL = "agricultural", "Agricultural"
    INDUSTRIAL = "industrial", "Industrial"


PROPERTY_TO_CIRCLE = {
    PropertyType.RESIDENTIAL_PLOT: CircleCategory.RESIDENTIAL,
    PropertyType.OLD_CONSTRUCTION: CircleCategory.RESIDENTIAL,
    PropertyType.COMMERCIAL_PLOT: CircleCategory.COMMERCIAL,
    PropertyType.AGRICULTURAL_LAND: CircleCategory.AGRICULTURAL,
    PropertyType.FARMHOUSE_LAND: CircleCategory.AGRICULTURAL,
    PropertyType.INDUSTRIAL_LAND: CircleCategory.INDUSTRIAL,
}


class AreaUnit(models.TextChoices):
    SQFT = "sqft", "Sq ft"
    SQYARD = "sqyard", "Sq yard (Gaj)"
    SQM = "sqm", "Sq metre"
    BISWA = "biswa", "Biswa"
    BIGHA = "bigha", "Bigha"
    ACRE = "acre", "Acre"
    HECTARE = "hectare", "Hectare"


class Status(models.TextChoices):
    NEW = "new", "New"
    CONTACTED = "contacted", "Contacted"
    VISIT_SCHEDULED = "visit_scheduled", "Site Visit Scheduled"
    VISIT_DONE = "visit_done", "Site Visit Done"
    UNDER_EVALUATION = "under_evaluation", "Under Evaluation"
    LEGAL_VERIFICATION = "legal_verification", "Legal Verification"
    OFFER_MADE = "offer_made", "Offer Made"
    NEGOTIATION = "negotiation", "Negotiation"
    OFFER_ACCEPTED = "offer_accepted", "Offer Accepted"
    ACQUIRED = "acquired", "Acquired"
    REJECTED = "rejected", "Rejected"
    WITHDREW = "withdrew", "Owner Withdrew"


# The happy-path order used for the owner timeline and funnel chart.
PIPELINE_ORDER = [
    Status.NEW,
    Status.CONTACTED,
    Status.VISIT_SCHEDULED,
    Status.VISIT_DONE,
    Status.UNDER_EVALUATION,
    Status.LEGAL_VERIFICATION,
    Status.OFFER_MADE,
    Status.NEGOTIATION,
    Status.OFFER_ACCEPTED,
    Status.ACQUIRED,
]
CLOSED_STATUSES = (Status.ACQUIRED, Status.REJECTED, Status.WITHDREW)

# One colour per status, used by the same badge partial in owner portal and dashboard.
STATUS_COLORS = {
    Status.NEW: "status-new",
    Status.CONTACTED: "status-contacted",
    Status.VISIT_SCHEDULED: "status-visit",
    Status.VISIT_DONE: "status-visit-done",
    Status.UNDER_EVALUATION: "status-eval",
    Status.LEGAL_VERIFICATION: "status-legal",
    Status.OFFER_MADE: "status-offer",
    Status.NEGOTIATION: "status-nego",
    Status.OFFER_ACCEPTED: "status-accepted",
    Status.ACQUIRED: "status-acquired",
    Status.REJECTED: "status-rejected",
    Status.WITHDREW: "status-withdrew",
}

OWNER_STATUS_HELP = {
    Status.NEW: "We have received your property details.",
    Status.CONTACTED: "Our team has spoken to you about the property.",
    Status.VISIT_SCHEDULED: "A field agent will visit the property on the scheduled date.",
    Status.VISIT_DONE: "Site visit completed. Report shared with evaluation team.",
    Status.UNDER_EVALUATION: "Our evaluators are checking price, demand and location.",
    Status.LEGAL_VERIFICATION: "Our legal team is verifying the title documents.",
    Status.OFFER_MADE: "We have made you an offer. Please respond from your dashboard.",
    Status.NEGOTIATION: "We are discussing the price with you.",
    Status.OFFER_ACCEPTED: "Offer accepted. Registry and payment are being arranged.",
    Status.ACQUIRED: "Registry done and payment completed. Thank you!",
    Status.REJECTED: "This property does not fit our current buying criteria.",
    Status.WITHDREW: "You chose not to proceed with this property.",
}
