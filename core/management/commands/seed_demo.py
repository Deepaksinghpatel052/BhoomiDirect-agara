"""
python manage.py seed_demo

Wipes the demo tables and creates realistic sample data for the client pitch:
users for every role, Agra tehsils/localities, SAMPLE circle rates, 40 owner
submissions across all pipeline stages, evaluations, visits, offers,
8 acquisitions (6 published), buyer inquiries, partners, blog posts, FAQs.
Placeholder photos are generated locally with Pillow (no internet needed).
"""
import random
import shutil
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from accounts.models import Notification, User
from acquisitions.models import (
    Acquisition,
    ActivityLog,
    Evaluation,
    InternalNote,
    LegalChecklist,
    Offer,
    SiteVisit,
)
from acquisitions.views import create_listing_from_acquisition
from blog.models import Category, Post
from core.models import FAQ, ContactMessage, SiteSettings, Testimonial
from listings.models import BuyerInquiry, Listing
from locations.models import CircleRate, Locality, LocalityFAQ, Tehsil
from locations.units import to_sq_meter
from partners.models import ChannelPartner
from submissions.constants import PIPELINE_ORDER, PROPERTY_TO_CIRCLE, CircleCategory, PropertyType, Status
from submissions.models import PropertySubmission, StatusHistory, SubmissionPhoto

from . import _demo_content as C

TEHSILS = ["Agra Sadar", "Etmadpur", "Kiraoli", "Kheragarh", "Fatehabad", "Bah", "Fatehpur Sikri"]

# 40 submissions: how many in each final status
STATUS_PLAN = (
    [Status.NEW] * 6 + [Status.CONTACTED] * 4 + [Status.VISIT_SCHEDULED] * 4 + [Status.VISIT_DONE] * 3
    + [Status.UNDER_EVALUATION] * 4 + [Status.LEGAL_VERIFICATION] * 3 + [Status.OFFER_MADE] * 3
    + [Status.NEGOTIATION] * 2 + [Status.OFFER_ACCEPTED] * 1 + [Status.ACQUIRED] * 8
    + [Status.REJECTED] * 1 + [Status.WITHDREW] * 1
)


class Command(BaseCommand):
    help = "Reset and load realistic demo data for BhoomiDirect Agra."

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=42, help="Random seed for repeatable data")

    def handle(self, *args, **options):
        self.rng = random.Random(options["seed"])
        self.now = timezone.now()
        self.media_demo = Path(settings.MEDIA_ROOT) / "demo"
        self.stdout.write("Resetting demo data...")
        self.reset()
        self.load_photo_library()
        with transaction.atomic():
            self.create_users()
            self.create_locations()
            self.create_partners()
            self.create_content()
            self.create_submissions()
            self.create_inquiries()
        self.print_summary()

    # ------------------------------------------------------------------
    def reset(self):
        for model in (
            BuyerInquiry, Listing, ActivityLog, InternalNote, Offer, Acquisition, Evaluation, LegalChecklist,
            SiteVisit, StatusHistory, PropertySubmission, ChannelPartner, CircleRate, LocalityFAQ, Locality,
            Tehsil, Post, Category, FAQ, Testimonial, ContactMessage, Notification, SiteSettings,
        ):
            model.objects.all().delete()
        User.objects.all().delete()
        for folder in ("demo", "submissions", "listings", "blog", "site_visits"):
            shutil.rmtree(Path(settings.MEDIA_ROOT) / folder, ignore_errors=True)
        shutil.rmtree(Path(settings.PRIVATE_MEDIA_ROOT), ignore_errors=True)
        self.media_demo.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    def create_users(self):
        R = User.Role
        self.admin = User.objects.create_superuser(
            "admin", "admin@bhoomidirect.demo", "admin123", first_name="Anil", last_name="Mehra", role=R.ADMIN,
            phone="9897011111",
        )
        self.evaluator = User.objects.create_user(
            "evaluator", "eval@bhoomidirect.demo", "demo123", first_name="Priyanka", last_name="Saxena",
            role=R.EVALUATOR, phone="9897022222",
        )
        self.agent = User.objects.create_user(
            "agent", "agent@bhoomidirect.demo", "demo123", first_name="Ravi", last_name="Yadav",
            role=R.FIELD_AGENT, phone="9897033333",
        )
        self.agent2 = User.objects.create_user(
            "agent2", "agent2@bhoomidirect.demo", "demo123", first_name="Sunil", last_name="Kushwah",
            role=R.FIELD_AGENT, phone="9897044444",
        )
        self.owner = User.objects.create_user(
            "owner", "owner@example.com", "demo123", first_name="Rajesh", last_name="Sharma",
            role=R.OWNER, phone="9876543210", whatsapp="9876543210",
        )
        self.partner_user = User.objects.create_user(
            "partner", "partner@example.com", "demo123", first_name="Manish", last_name="Agrawal",
            role=R.CHANNEL_PARTNER, phone="9811122233",
        )
        self.agents = [self.agent, self.agent2]

    # ------------------------------------------------------------------
    def create_locations(self):
        self.tehsils = {name: Tehsil.objects.create(name=name) for name in TEHSILS}
        self.localities = []
        year = self.now.year
        for name, tehsil, ltype, lat, lng, featured, res_rate, agri_rate in C.LOCALITIES:
            desc, connectivity, landmarks = C.LOCALITY_TEXT[name]
            loc = Locality.objects.create(
                name=name, tehsil=self.tehsils[tehsil], locality_type=ltype, latitude=lat, longitude=lng,
                description=desc, connectivity=connectivity, landmarks=landmarks, is_featured=featured,
            )
            CircleRate.objects.create(locality=loc, property_type=CircleCategory.RESIDENTIAL, rate_per_sq_meter=res_rate, effective_year=year)
            if ltype in ("urban", "highway"):
                CircleRate.objects.create(locality=loc, property_type=CircleCategory.COMMERCIAL, rate_per_sq_meter=round(res_rate * 1.7, -2), effective_year=year)
            if ltype == "highway":
                CircleRate.objects.create(locality=loc, property_type=CircleCategory.INDUSTRIAL, rate_per_sq_meter=round(res_rate * 0.55, -2), effective_year=year)
            if agri_rate:
                CircleRate.objects.create(locality=loc, property_type=CircleCategory.AGRICULTURAL, rate_per_sq_meter=agri_rate, effective_year=year)
            faqs = [
                (f"Do you buy land in {name}?", f"Yes. We actively buy plots and land in {name} ({tehsil} tehsil). Submit your details and our local field agent will visit within 3 days."),
                (f"What is the price of land in {name}?", f"Prices in {name} depend on road width, size and legal status. Use our free price estimator for an indicative range, then get an exact written offer after a site visit."),
                (f"How long does it take to sell my property in {name}?", "Most deals close in 2 to 4 weeks after the documents are verified. Payment is made in full at registry."),
            ]
            for i, (q, a) in enumerate(faqs):
                LocalityFAQ.objects.create(locality=loc, question=q, answer=a, order=i)
            self.localities.append(loc)
        self.loc_by_name = {loc.name: loc for loc in self.localities}

    # ------------------------------------------------------------------
    def create_partners(self):
        L = self.loc_by_name
        data = [
            (self.partner_user, "Manish Agrawal", "Agrawal Property Point", "9811122233", "UPRERAAGT12345", 9, True, ["Fatehabad Road", "Tajganj", "Shamshabad Road"]),
            (None, "Sanjeev Tyagi", "Tyagi Estates", "9837011223", "UPRERAAGT20441", 12, True, ["Sikandra", "Runkata", "Artoni"]),
            (None, "Farhan Qureshi", "Qureshi Land Consultants", "9759033445", "", 6, True, ["Agra-Lucknow Expressway Belt", "Etmadpur"]),
            (None, "Deepak Chahar", "Chahar Associates", "9917055667", "", 3, False, ["Kiraoli", "Fatehpur Sikri"]),
        ]
        self.partners = []
        for user, name, firm, phone, rera, exp, approved, areas in data:
            p = ChannelPartner.objects.create(
                user=user, name=name, firm_name=firm, phone=phone, rera_agent_number=rera,
                experience_years=exp, is_approved=approved, email=f"{name.split()[0].lower()}@example.com",
            )
            p.areas_covered.set([L[a] for a in areas])
            self.partners.append(p)

    # ------------------------------------------------------------------
    def create_content(self):
        SiteSettings.objects.create(properties_acquired=186, acres_evaluated=1250, payout_crore=Decimal("96.5"), avg_days_to_close=21)
        for i, (name, loc, prop, quote) in enumerate(C.TESTIMONIALS):
            Testimonial.objects.create(name=name, location=loc, property_sold=prop, quote=quote, rating=5 if i != 2 else 4, order=i)
        for i, (cat, q, a, home) in enumerate(C.FAQS):
            FAQ.objects.create(category=cat, question=q, answer=a, show_on_home=home, order=i)
        cats = {name: Category.objects.create(name=name) for name in C.BLOG_CATEGORIES}
        for i, post in enumerate(C.BLOG_POSTS):
            p = Post(
                title=post["title"], category=cats[post["category"]], excerpt=post["excerpt"],
                content=post["content"].strip(), published_at=self.now - timedelta(days=6 + i * 9),
                meta_title=f"{post['title']} | BhoomiDirect Agra",
                meta_description=post["excerpt"][:155],
            )
            cover_theme = ["agri", "agri", "plot", "house", "farm", "road"][i % 6]
            p.cover_image.name = self.next_photo(cover_theme) or self.make_image(
                f"blog-{i}.jpg", ["field", "plot", "road"][i % 3], post["title"], banner=True
            )
            p.save()
        ContactMessage.objects.create(name="Alok Verma", phone="9758811223", subject="Land in Bah", message="I have 12 bigha land in Bah tehsil. Do you buy there?")
        ContactMessage.objects.create(name="Shalini Jain", phone="9634455667", subject="Plot documents", message="My plot registry is in my late father's name. Can I still sell?")

    # ------------------------------------------------------------------
    def pick_area(self, ptype):
        r = self.rng
        if ptype == PropertyType.RESIDENTIAL_PLOT:
            return r.choice([100, 120, 150, 200, 250, 300, 400]), "sqyard"
        if ptype == PropertyType.OLD_CONSTRUCTION:
            return r.choice([1800, 2200, 2700, 3200]), "sqft"
        if ptype == PropertyType.COMMERCIAL_PLOT:
            return r.choice([200, 300, 500, 800]), "sqyard"
        if ptype == PropertyType.AGRICULTURAL_LAND:
            unit = r.choice(["bigha", "bigha", "biswa", "acre"])
            value = {"bigha": r.choice([2, 3, 4, 5, 8, 12]), "biswa": r.choice([10, 15, 30]), "acre": r.choice([1.5, 2, 3, 5])}[unit]
            return value, unit
        if ptype == PropertyType.FARMHOUSE_LAND:
            unit = r.choice(["bigha", "acre"])
            return (r.choice([1, 2, 3]) if unit == "bigha" else r.choice([1, 1.5])), unit
        if ptype == PropertyType.INDUSTRIAL_LAND:
            return r.choice([0.5, 1, 2, 1.2]), r.choice(["acre", "hectare"])
        return 200, "sqyard"

    def pick_type(self, loc):
        r = self.rng
        if loc.locality_type == "urban":
            return r.choice([PropertyType.RESIDENTIAL_PLOT] * 3 + [PropertyType.COMMERCIAL_PLOT, PropertyType.OLD_CONSTRUCTION])
        if loc.locality_type == "highway":
            return r.choice([PropertyType.AGRICULTURAL_LAND, PropertyType.FARMHOUSE_LAND, PropertyType.INDUSTRIAL_LAND,
                             PropertyType.COMMERCIAL_PLOT, PropertyType.RESIDENTIAL_PLOT])
        return r.choice([PropertyType.AGRICULTURAL_LAND] * 3 + [PropertyType.RESIDENTIAL_PLOT, PropertyType.FARMHOUSE_LAND])

    def market_price(self, loc, ptype, area_value, unit, factor):
        sq_m = to_sq_meter(area_value, unit)
        rate = loc.rate_for(PROPERTY_TO_CIRCLE[ptype]) or loc.rate_for(CircleCategory.RESIDENTIAL)
        price = rate.rate_per_sq_meter * sq_m * Decimal(str(factor))
        return Decimal(max(200000, round(price / 50000) * 50000))

    def create_submissions(self):
        r = self.rng
        plan = list(STATUS_PLAN)
        # Owner demo account: first three submissions (ref 00001 has an open offer to respond to)
        owner_plan = [Status.OFFER_MADE, Status.UNDER_EVALUATION, Status.ACQUIRED]
        for s in owner_plan:
            plan.remove(s)
        r.shuffle(plan)
        plan = owner_plan + plan
        owner_locs = ["Shamshabad Road", "Fatehabad Road", "Sikandra"]
        owner_types = [PropertyType.AGRICULTURAL_LAND, PropertyType.RESIDENTIAL_PLOT, PropertyType.RESIDENTIAL_PLOT]

        self.acquisitions = []
        names = list(C.OWNER_NAMES)
        r.shuffle(names)
        for i, status in enumerate(plan):
            is_owner = i < 3
            loc = self.loc_by_name[owner_locs[i]] if is_owner else r.choice(self.localities)
            ptype = owner_types[i] if is_owner else self.pick_type(loc)
            if PROPERTY_TO_CIRCLE[ptype] == CircleCategory.COMMERCIAL and not loc.rate_for(CircleCategory.COMMERCIAL):
                ptype = PropertyType.RESIDENTIAL_PLOT
            if PROPERTY_TO_CIRCLE[ptype] == CircleCategory.AGRICULTURAL and not loc.rate_for(CircleCategory.AGRICULTURAL):
                ptype = PropertyType.RESIDENTIAL_PLOT
            if PROPERTY_TO_CIRCLE[ptype] == CircleCategory.INDUSTRIAL and not loc.rate_for(CircleCategory.INDUSTRIAL):
                ptype = PropertyType.COMMERCIAL_PLOT
            area_value, unit = self.pick_area(ptype)
            stage = PIPELINE_ORDER.index(status) if status in PIPELINE_ORDER else 4
            # Older leads have progressed further
            days_ago = {0: r.randint(0, 6), 1: r.randint(3, 12), 2: r.randint(5, 15), 3: r.randint(8, 20)}.get(stage, r.randint(15 + stage * 3, 30 + stage * 5))
            if status == Status.NEW and i % 3 == 0:
                days_ago = 0
            created = self.now - timedelta(days=days_ago, hours=r.randint(1, 9))
            is_agri = ptype in (PropertyType.AGRICULTURAL_LAND, PropertyType.FARMHOUSE_LAND)
            name = "Rajesh Sharma" if is_owner else names[i % len(names)]
            phone = "9876543210" if is_owner else f"{r.choice('6789')}{r.randint(100000000, 999999999)}"
            expected = self.market_price(loc, ptype, area_value, unit, r.uniform(1.25, 1.7))
            source = r.choice(["website"] * 5 + ["whatsapp", "referral", "partner"])
            joint = r.random() < 0.3
            sub = PropertySubmission.objects.create(
                owner_user=self.owner if is_owner else None,
                owner_name=name, phone=phone, whatsapp=phone, email=f"{name.split()[0].lower()}@example.com" if r.random() < 0.5 else "",
                relation=r.choice(["owner"] * 4 + ["co_owner", "family", "poa"]), phone_verified=True,
                property_type=ptype, tehsil=loc.tehsil, locality=loc,
                village_colony=r.choice(["", "Gram " + loc.name.split()[0], "Sector 4", "Green Park Colony", "Shiv Vihar", "Pushp Vihar"]) if not is_agri else f"Mauza {r.choice(['Rohta', 'Barara', 'Nagla Kali', 'Kakua', 'Dhanauli', 'Midhakur'])}",
                khasra_number=f"{r.randint(12, 980)}{r.choice(['', '/1', '/2', 'Ka'])}" if is_agri or r.random() < 0.4 else "",
                landmark=r.choice(["Near petrol pump", "Behind primary school", "Opposite temple", "Near canal bridge", "Main road facing"]),
                address=f"{loc.name}, {loc.tehsil.name}, Agra",
                latitude=Decimal(str(float(loc.latitude) + r.uniform(-0.012, 0.012))).quantize(Decimal("0.000001")),
                longitude=Decimal(str(float(loc.longitude) + r.uniform(-0.012, 0.012))).quantize(Decimal("0.000001")),
                area_value=Decimal(str(area_value)), area_unit=unit,
                road_width_ft=r.choice([12, 20, 25, 30, 40, 60]), frontage_ft=r.choice([None, 30, 40, 50, 80, 120]),
                facing=r.choice(["east", "north", "west", "south", "north_east"]),
                is_corner=r.random() < 0.25, has_boundary_wall=r.random() < 0.5, has_electricity=r.random() < 0.6,
                water_source=r.choice(["municipal", "borewell", "handpump", "none"]),
                distance_main_road_m=r.choice([0, 50, 200, 500, 1200]),
                irrigation_source=r.choice(["tubewell", "canal", "rain"]) if is_agri else "",
                current_crop=r.choice(C.CROPS) if is_agri else "",
                soil_type=r.choice(["alluvial", "sandy", "mixed"]) if is_agri else "",
                has_tubewell=is_agri and r.random() < 0.5,
                ownership_type="joint" if joint else "single", number_of_owners=r.randint(2, 4) if joint else 1,
                title_documents=r.sample(["registry", "khatauni", "gpa", "will"], k=r.randint(1, 2)) if not is_agri else ["khatauni", "registry"],
                mutation_done=r.choice(["yes", "yes", "no", "not_sure"]),
                approval_status=("na" if is_agri else r.choice(["ada", "not_approved", "not_sure"])),
                has_loan=r.random() < 0.1, has_dispute=False,
                expected_price=expected, price_negotiable=r.random() < 0.8,
                reason_for_selling=r.choice(C.REASONS), urgency=r.choice(["1_month", "1_3_months", "1_3_months", "exploring"]),
                preferred_visit_time=r.choice(["morning", "afternoon", "evening", "weekend"]),
                consent=True, status=Status.NEW, source=source,
                referred_by=r.choice(self.partners[:3]) if source == "partner" else None,
                is_complete=not (status == Status.NEW and i % 4 == 1),
                created_at=created,
            )
            if sub.has_loan:
                sub.encumbrance_details = "Kisan credit card loan of about ₹ 2 lakh, will be closed at registry."
            # Photos: real library photos matched to the property type
            images = self.photos_for(sub, r.randint(2, 3)) if self.photos else []
            if not images:
                theme = "field" if is_agri else r.choice(["plot", "road", "plot"])
                images = [
                    self.make_image(f"sub-{sub.pk}-{n}.jpg", theme, f"{loc.name} · {sub.get_property_type_display()}", seed=sub.pk * 10 + n)
                    for n in range(2)
                ]
            for n, img in enumerate(images):
                SubmissionPhoto.objects.create(submission=sub, image=img, caption=f"Photo {n + 1}")
            self.build_pipeline(sub, status, created)

    # ------------------------------------------------------------------
    def build_pipeline(self, sub, final_status, created):
        r = self.rng
        if final_status == Status.REJECTED:
            chain = [Status.NEW, Status.CONTACTED, Status.VISIT_SCHEDULED, Status.VISIT_DONE, Status.UNDER_EVALUATION, Status.REJECTED]
        elif final_status == Status.WITHDREW:
            chain = [Status.NEW, Status.CONTACTED, Status.WITHDREW]
        else:
            chain = PIPELINE_ORDER[: PIPELINE_ORDER.index(final_status) + 1]

        span = max((self.now - created).total_seconds(), 3600)
        step = span / (len(chain) + 0.5)
        times = [created + timedelta(seconds=step * k) for k in range(len(chain))]
        agent = r.choice(self.agents) if len(chain) > 1 else None
        if agent:
            sub.assigned_agent = agent
        notes = {
            Status.NEW: "Submitted via website",
            Status.CONTACTED: "Spoke to owner, documents available",
            Status.VISIT_SCHEDULED: "Site visit fixed with owner",
            Status.VISIT_DONE: "Site visit completed",
            Status.UNDER_EVALUATION: "Evaluation started",
            Status.LEGAL_VERIFICATION: "Documents sent to legal desk",
            Status.OFFER_MADE: "Offer shared with owner",
            Status.NEGOTIATION: "Owner sent counter offer",
            Status.OFFER_ACCEPTED: "Owner accepted offer",
            Status.ACQUIRED: "Registry done, payment released",
            Status.REJECTED: "Title chain unclear, does not fit buying criteria",
            Status.WITHDREW: "Owner decided to keep the land",
        }
        prev = ""
        for status, ts in zip(chain, times):
            by = None if status == Status.NEW else (agent if status in (Status.CONTACTED, Status.VISIT_SCHEDULED, Status.VISIT_DONE) else self.evaluator)
            if status == Status.ACQUIRED:
                by = self.admin
            StatusHistory.objects.create(submission=sub, old_status=prev, new_status=status, note=notes[status], changed_by=by, timestamp=ts)
            ActivityLog.objects.create(submission=sub, user=by, action=f"Status changed to {Status(status).label}", details=notes[status], created_at=ts)
            prev = status
        sub.status = final_status
        sub.save(update_fields=["status", "assigned_agent"])

        reached = set(chain)
        t = dict(zip(chain, times))
        # Site visit
        if Status.VISIT_SCHEDULED in reached:
            done = Status.VISIT_DONE in reached
            when = (t.get(Status.VISIT_DONE) or (self.now + timedelta(days=r.randint(1, 5)))).replace(hour=r.choice([10, 11, 15, 16]), minute=0)
            SiteVisit.objects.create(
                submission=sub, agent=agent, scheduled_for=when,
                status=SiteVisit.VisitStatus.COMPLETED if done else SiteVisit.VisitStatus.SCHEDULED,
                visit_notes="Boundary pillars present. Owner showed original documents. Approach road is pucca." if done else "",
                boundary_matches_documents=done, road_access_confirmed=done, no_encroachment=done and r.random() < 0.85,
                owner_met_in_person=done, neighbour_feedback="Neighbours confirm ownership, no dispute." if done else "",
            )
        # Evaluation
        if Status.UNDER_EVALUATION in reached:
            strong = final_status in (Status.ACQUIRED, Status.OFFER_ACCEPTED, Status.NEGOTIATION, Status.OFFER_MADE)
            low = final_status == Status.REJECTED
            def score():
                return r.randint(7, 10) if strong else (r.randint(2, 5) if low else r.randint(4, 8))
            ev = Evaluation(
                submission=sub, evaluator=self.evaluator,
                location_potential=score(), road_access=score(), legal_clarity=score() if not low else 2,
                price_vs_market=score(), resale_demand=score(), development_nearby=score(),
                estimated_resale_value=(sub.expected_price * Decimal(str(r.uniform(1.12, 1.35)))).quantize(Decimal("1")),
                remarks="Good road access and steady demand in the belt." if strong else "Average location, check pricing.",
            )
            ev.save()
        # Legal
        if Status.LEGAL_VERIFICATION in reached:
            full = Status.OFFER_MADE in reached
            LegalChecklist.objects.create(
                submission=sub, title_verified=True, khatauni_matched=True, no_encumbrance=full or r.random() < 0.5,
                mutation_verified=full, owner_id_verified=True, noc_obtained=full and r.random() < 0.7,
                notes="30-year title chain checked at sub-registrar office.", verified_by=self.evaluator,
            )
        # Offers
        if Status.OFFER_MADE in reached:
            amount = (sub.expected_price * Decimal(str(r.uniform(0.86, 0.95))) / 10000).quantize(Decimal("1")) * 10000
            offer = Offer.objects.create(
                submission=sub, amount=amount, valid_till=(t[Status.OFFER_MADE] + timedelta(days=12)).date(),
                created_by=self.evaluator, created_at=t[Status.OFFER_MADE],
            )
            if final_status == Status.OFFER_MADE:
                offer.valid_till = timezone.localdate() + timedelta(days=10)
                offer.save()
            elif final_status == Status.NEGOTIATION:
                offer.status = Offer.OfferStatus.COUNTERED
                offer.owner_counter_amount = (sub.expected_price / 10000).quantize(Decimal("1")) * 10000
                offer.owner_note = "My neighbour got a better rate last month."
                offer.responded_at = t[Status.NEGOTIATION]
                offer.save()
            else:
                offer.status = Offer.OfferStatus.ACCEPTED
                offer.responded_at = t.get(Status.OFFER_ACCEPTED, t[Status.OFFER_MADE])
                offer.save()
        # Acquisition
        if final_status == Status.ACQUIRED:
            offer = sub.offers.first()
            price = offer.amount
            purchase_date = t[Status.ACQUIRED].date()
            acq = Acquisition.objects.create(
                submission=sub, purchase_price=price, purchase_date=purchase_date, registry_date=purchase_date,
                payment_mode=r.choice(["rtgs", "rtgs", "mixed"]), stamp_duty=(price * Decimal("0.07")).quantize(Decimal("1")),
                registration_fee=(price * Decimal("0.01")).quantize(Decimal("1")), other_costs=Decimal(r.choice([15000, 25000, 40000])),
                created_by=self.admin, notes="Registry at Sub-Registrar office, Agra.",
            )
            self.acquisitions.append(acq)
        # Internal note on active leads
        if len(chain) > 2 and r.random() < 0.6:
            InternalNote.objects.create(submission=sub, author=agent or self.evaluator, text=r.choice([
                "Owner prefers calls after 5 pm.", "Two brothers are co-owners, both agree.",
                "Nearby plot sold at similar rate last month.", "Ask for latest khatauni copy.",
            ]))
        # Notifications for the demo owner
        if sub.owner_user_id:
            for status in chain[-2:]:
                Notification.objects.create(
                    user=self.owner, title=f"{sub.reference_id}: {Status(status).label}", message=notes[status],
                    url=sub.get_absolute_url(), is_read=status != chain[-1],
                )

    # ------------------------------------------------------------------
    def create_inquiries(self):
        r = self.rng
        # Move the two latest acquisitions into the current month (for the KPI), then publish 6 of 8
        self.acquisitions.sort(key=lambda a: a.purchase_date)
        today = timezone.localdate()
        for k, acq in enumerate(self.acquisitions[-2:]):
            acq.purchase_date = acq.registry_date = today - timedelta(days=min(k + 1, today.day - 1))
            acq.save()
        self.listings = []
        for k, acq in enumerate(self.acquisitions[:6]):
            listing = create_listing_from_acquisition(acq, markup=r.uniform(1.18, 1.35))
            listing.created_at = self.now - timedelta(days=r.randint(2, 30))
            listing.is_featured = k < 3
            listing.save()
            self.listings.append(listing)
        # One booked and one sold for profit reporting
        self.listings[0].status = Listing.ListingStatus.SOLD
        self.listings[0].sold_price = (self.listings[0].price * Decimal("0.97")).quantize(Decimal("1"))
        self.listings[0].sold_date = timezone.localdate() - timedelta(days=5)
        self.listings[0].save()
        self.listings[1].status = Listing.ListingStatus.BOOKED
        self.listings[1].save()

        statuses = [s for s, _ in BuyerInquiry.InquiryStatus.choices]
        available = self.listings[1:]
        for i, name in enumerate(C.BUYER_NAMES):
            listing = available[i % len(available)]
            BuyerInquiry.objects.create(
                listing=listing, name=name, phone=f"9{r.randint(100000000, 999999999)}",
                budget=(listing.price * Decimal(str(r.uniform(0.85, 1.05))) / 10000).quantize(Decimal("1")) * 10000,
                message=r.choice(["Please share more photos.", "Is the price negotiable?", "Want a site visit this Sunday.", "Interested, please call."]),
                status=statuses[i % len(statuses)], referred_by=self.partners[i % 3] if i % 3 == 0 else None,
                created_at=self.now - timedelta(days=r.randint(0, 20)),
            )

    # ------------------------------------------------------------------
    # Real photo library (static/img/photos, filled by `manage.py fetch_photos`)
    TYPE_THEMES = {
        PropertyType.RESIDENTIAL_PLOT: ["plot", "plot", "house"],
        PropertyType.COMMERCIAL_PLOT: ["plot", "commercial", "road"],
        PropertyType.AGRICULTURAL_LAND: ["agri", "agri", "farm"],
        PropertyType.FARMHOUSE_LAND: ["farm", "agri", "farm"],
        PropertyType.INDUSTRIAL_LAND: ["plot", "road", "road"],
        PropertyType.OLD_CONSTRUCTION: ["house", "house", "plot"],
    }

    def load_photo_library(self):
        """Copy the real photos into MEDIA so ImageFields can point at them."""
        src = Path(settings.BASE_DIR) / "static" / "img" / "photos"
        dest = self.media_demo / "photos"
        dest.mkdir(parents=True, exist_ok=True)
        self.photos = {}
        for f in sorted(src.glob("*.jpg")):
            shutil.copy2(f, dest / f.name)
            self.photos.setdefault(f.stem.rsplit("-", 1)[0], []).append(f"demo/photos/{f.name}")
        for items in self.photos.values():
            self.rng.shuffle(items)
        self.photo_cursor = {}
        if self.photos:
            self.stdout.write(f"Using {sum(map(len, self.photos.values()))} real photos from static/img/photos")
        else:
            self.stdout.write(self.style.WARNING("No real photos found (run `manage.py fetch_photos`); using generated placeholders."))

    def next_photo(self, theme):
        """Rotate through a theme so neighbouring properties don't share photos."""
        items = self.photos.get(theme) or self.photos.get("plot") or []
        if not items:
            return None
        i = self.photo_cursor.get(theme, 0)
        self.photo_cursor[theme] = i + 1
        return items[i % len(items)]

    def photos_for(self, sub, count):
        themes = list(self.TYPE_THEMES[sub.property_type])
        if sub.locality.locality_type == "highway" and sub.property_type != PropertyType.OLD_CONSTRUCTION:
            themes[-1] = "road"
        chosen = []
        for theme in themes[:count]:
            photo = self.next_photo(theme)
            if photo and photo not in chosen:
                chosen.append(photo)
        return chosen

    # ------------------------------------------------------------------
    PALETTES = {
        "field": [((176, 206, 230), (238, 230, 205)), ((120, 160, 70), (200, 180, 90))],
        "plot": [((190, 215, 235), (245, 236, 215)), ((196, 168, 120), (160, 130, 90))],
        "road": [((200, 220, 238), (248, 240, 222)), ((150, 160, 130), (110, 110, 105))],
    }

    def make_image(self, filename, theme, label, seed=0, banner=False):
        """Draw a simple landscape placeholder (sky, ground, details) and return the media-relative path."""
        r = random.Random(seed or hash(filename) % 10000)
        w, h = (1200, 675) if banner else (960, 600)
        img = Image.new("RGB", (w, h))
        draw = ImageDraw.Draw(img)
        (sky_top, sky_bottom), (ground_top, ground_bottom) = self.PALETTES[theme]
        horizon = int(h * r.uniform(0.42, 0.55))
        for y in range(h):
            if y < horizon:
                t = y / horizon
                c = tuple(int(sky_top[i] + (sky_bottom[i] - sky_top[i]) * t) for i in range(3))
            else:
                t = (y - horizon) / (h - horizon)
                c = tuple(int(ground_top[i] + (ground_bottom[i] - ground_top[i]) * t) for i in range(3))
            draw.line([(0, y), (w, y)], fill=c)
        # sun
        sx = r.randint(int(w * 0.6), int(w * 0.9))
        draw.ellipse([sx, 40, sx + 70, 110], fill=(246, 214, 140))
        # distant tree line
        for x in range(0, w, 18):
            th = r.randint(10, 34)
            draw.ellipse([x, horizon - th, x + 30, horizon + 6], fill=(70, 110, 70))
        if theme == "field":
            for k in range(14):
                y = horizon + 12 + k * (h - horizon) // 14
                draw.line([(0, y), (w, y + r.randint(-6, 6))], fill=(90, 130, 50), width=3)
        elif theme == "plot":
            x0, y0 = int(w * 0.18), horizon + 40
            x1, y1 = int(w * 0.82), h - 50
            draw.polygon([(x0, y1), (x0 + 80, y0), (x1 - 80, y0), (x1, y1)], outline=(181, 80, 47), width=5)
            for px, py in [(x0, y1), (x0 + 80, y0), (x1 - 80, y0), (x1, y1)]:
                draw.rectangle([px - 6, py - 22, px + 6, py], fill=(230, 230, 225), outline=(120, 120, 120))
        else:
            draw.polygon([(w * 0.42, h), (w * 0.49, horizon), (w * 0.51, horizon), (w * 0.62, h)], fill=(85, 85, 85))
            for k in range(6):
                y = horizon + 20 + k * (h - horizon) // 6
                draw.line([(w * 0.5, y), (w * 0.5, y + 14)], fill=(240, 240, 240), width=4)
        img = img.filter(ImageFilter.SMOOTH)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.load_default(size=30 if banner else 24)
            small = ImageFont.load_default(size=18)
        except TypeError:  # very old Pillow
            font = small = ImageFont.load_default()
        text = label if len(label) < 70 else label[:67] + "..."
        draw.rectangle([0, h - 64, w, h], fill=(19, 61, 40))
        draw.text((24, h - 50), text, fill=(255, 255, 255), font=font)
        draw.text((w - 210, h - 44), "DEMO PHOTO", fill=(200, 150, 62), font=small)
        path = self.media_demo / filename
        img.save(path, "JPEG", quality=78, optimize=True)
        return f"demo/{filename}"

    # ------------------------------------------------------------------
    def print_summary(self):
        s = self.style.SUCCESS
        self.stdout.write(s("Demo data ready."))
        self.stdout.write(f"  Tehsils: {Tehsil.objects.count()}  Localities: {Locality.objects.count()}  Sample circle rates: {CircleRate.objects.count()}")
        self.stdout.write(f"  Submissions: {PropertySubmission.objects.count()}  Acquisitions: {Acquisition.objects.count()}  Listings: {Listing.objects.count()}")
        self.stdout.write(f"  Buyer inquiries: {BuyerInquiry.objects.count()}  Partners: {ChannelPartner.objects.count()}  Blog posts: {Post.objects.count()}")
        self.stdout.write("  Logins: admin/admin123, evaluator/demo123, agent/demo123, owner/demo123, partner/demo123")
