from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from acquisitions.models import Acquisition, Evaluation, LegalChecklist, Offer
from core.tests.helpers import make_locality, make_submission, make_user
from listings.models import Listing
from submissions.constants import Status


class EvaluationScoreTests(TestCase):
    def test_calculate(self):
        self.assertEqual(Evaluation.calculate([8, 8, 8, 8, 8, 8]), (48, "strong_buy"))
        self.assertEqual(Evaluation.calculate([7, 7, 7, 8, 8, 8]), (45, "strong_buy"))
        self.assertEqual(Evaluation.calculate([5, 5, 5, 5, 5, 5]), (30, "consider"))
        self.assertEqual(Evaluation.calculate([5, 5, 5, 5, 5, 4]), (29, "reject"))

    def test_save_computes_total_circle_value_and_margin(self):
        loc = make_locality()
        sub = make_submission(loc)  # 200 gaj, expected 50 lakh
        ev = Evaluation.objects.create(
            submission=sub, location_potential=9, road_access=8, legal_clarity=8, price_vs_market=7,
            resale_demand=8, development_nearby=7, estimated_resale_value=Decimal("6000000"),
        )
        self.assertEqual(ev.total_score, 47)
        self.assertEqual(ev.recommendation, Evaluation.Recommendation.STRONG_BUY)
        self.assertEqual(ev.circle_rate_value, Decimal("5016900"))
        self.assertEqual(ev.margin_percent, 20.0)

    def test_legal_progress(self):
        sub = make_submission(make_locality())
        checklist = LegalChecklist.objects.create(submission=sub, title_verified=True, khatauni_matched=True, owner_id_verified=True)
        self.assertEqual(checklist.progress, 50)


class PermissionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.loc = make_locality()
        cls.owner = make_user("owner1", User.Role.OWNER, "9876500101")
        cls.other_owner = make_user("owner2", User.Role.OWNER, "9876500102")
        cls.agent = make_user("agent1", User.Role.FIELD_AGENT, "9876500103")
        cls.evaluator = make_user("eval1", User.Role.EVALUATOR, "9876500104")
        cls.admin = make_user("admin1", User.Role.ADMIN, "9876500105")
        cls.sub = make_submission(cls.loc, owner_user=cls.owner, phone="9876500101")

    def login(self, user):
        self.client.force_login(user)

    def test_dashboard_requires_staff(self):
        url = reverse("dashboard:overview")
        self.assertEqual(self.client.get(url).status_code, 302)
        self.login(self.owner)
        self.assertEqual(self.client.get(url).status_code, 403)
        for user in (self.agent, self.evaluator, self.admin):
            self.login(user)
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_owner_sees_only_own_submissions(self):
        url = reverse("submissions:owner_submission", args=[self.sub.reference_id])
        self.login(self.owner)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.login(self.other_owner)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_field_agent_cannot_evaluate_or_make_offer(self):
        self.login(self.agent)
        r = self.client.post(reverse("dashboard:evaluation_save", args=[self.sub.pk]), {f: 8 for f in Evaluation.SCORE_FIELDS})
        self.assertEqual(r.status_code, 403)
        r = self.client.post(reverse("dashboard:offer_create", args=[self.sub.pk]), {"amount": 100, "valid_till": timezone.localdate()})
        self.assertEqual(r.status_code, 403)

    def test_only_admin_can_acquire_and_export_restricted(self):
        self.login(self.evaluator)
        self.assertEqual(self.client.post(reverse("dashboard:acquire", args=[self.sub.pk]), {}).status_code, 403)
        self.assertEqual(self.client.get(reverse("dashboard:leads_export")).status_code, 200)
        self.login(self.agent)
        self.assertEqual(self.client.get(reverse("dashboard:leads_export")).status_code, 403)

    def test_private_documents_not_public(self):
        from django.core.files.base import ContentFile
        from submissions.models import SubmissionDocument
        import shutil
        from django.test import override_settings

        with override_settings(PRIVATE_MEDIA_ROOT="test_private_tmp2"):
            doc = SubmissionDocument(submission=self.sub, doc_type="registry")
            doc.file.save("deed.pdf", ContentFile(b"%PDF-1.4 demo"))
            url = reverse("submissions:document_download", args=[doc.pk])
            self.assertEqual(self.client.get(url).status_code, 302)
            self.login(self.other_owner)
            self.assertEqual(self.client.get(url).status_code, 404)
            self.login(self.owner)
            self.assertEqual(self.client.get(url).status_code, 200)
            self.login(self.agent)
            self.assertEqual(self.client.get(url).status_code, 200)
        shutil.rmtree("test_private_tmp2", ignore_errors=True)


class EndToEndBusinessFlowTests(TestCase):
    """Owner submits -> staff evaluates -> offer -> owner accepts -> acquired -> published -> buyer inquiry."""

    def test_full_flow(self):
        loc = make_locality()
        owner = make_user("ownerx", User.Role.OWNER, "9876500201")
        evaluator = make_user("evalx", User.Role.EVALUATOR, "9876500202")
        agent = make_user("agentx", User.Role.FIELD_AGENT, "9876500203")
        admin = make_user("adminx", User.Role.ADMIN, "9876500204")
        sub = make_submission(loc, owner_user=owner, phone="9876500201")

        # Agent moves on Kanban and schedules a visit
        self.client.force_login(agent)
        r = self.client.post(reverse("dashboard:pipeline_move"), {"pk": sub.pk, "status": Status.CONTACTED})
        self.assertTrue(r.json()["ok"])
        r = self.client.post(reverse("dashboard:pipeline_move"), {"pk": sub.pk, "status": Status.ACQUIRED})
        self.assertEqual(r.status_code, 400)
        when = (timezone.localtime() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        self.client.post(reverse("dashboard:visit_create", args=[sub.pk]), {"agent": agent.pk, "scheduled_for": when})
        sub.refresh_from_db()
        self.assertEqual(sub.status, Status.VISIT_SCHEDULED)
        visit = sub.site_visits.get()
        self.client.post(reverse("dashboard:visit_report", args=[visit.pk]), {"status": "completed", "visit_notes": "OK", "road_access_confirmed": "on"})
        sub.refresh_from_db()
        self.assertEqual(sub.status, Status.VISIT_DONE)

        # Evaluator scores, verifies legal, and makes an offer
        self.client.force_login(evaluator)
        scores = {f: 8 for f in Evaluation.SCORE_FIELDS}
        self.client.post(reverse("dashboard:evaluation_save", args=[sub.pk]), {**scores, "estimated_resale_value": "6500000"})
        self.client.post(reverse("dashboard:legal_save", args=[sub.pk]), {"title_verified": "on", "khatauni_matched": "on"})
        valid = (timezone.localdate() + timedelta(days=7)).isoformat()
        self.client.post(reverse("dashboard:offer_create", args=[sub.pk]), {"amount": "4800000", "valid_till": valid, "terms": "Full payment"})
        sub.refresh_from_db()
        self.assertEqual(sub.status, Status.OFFER_MADE)
        self.assertEqual(sub.evaluation.recommendation, "strong_buy")
        offer = sub.offers.get()

        # Owner counters, then accepts a revised offer
        self.client.force_login(owner)
        self.client.post(reverse("submissions:offer_respond", args=[offer.pk]), {"action": "counter", "counter_amount": "5000000"})
        offer.refresh_from_db()
        self.assertEqual(offer.status, Offer.OfferStatus.COUNTERED)
        self.client.force_login(evaluator)
        self.client.post(reverse("dashboard:offer_create", args=[sub.pk]), {"amount": "4900000", "valid_till": valid})
        new_offer = sub.offers.filter(status="pending").get()
        self.client.force_login(owner)
        self.client.post(reverse("submissions:offer_respond", args=[new_offer.pk]), {"action": "accept"})
        sub.refresh_from_db()
        self.assertEqual(sub.status, Status.OFFER_ACCEPTED)
        self.assertTrue(owner.notifications.exists())

        # Admin records purchase and publishes for resale
        self.client.force_login(admin)
        self.client.post(reverse("dashboard:acquire", args=[sub.pk]), {
            "purchase_price": "4900000", "purchase_date": timezone.localdate().isoformat(), "payment_mode": "rtgs",
            "stamp_duty": "343000", "registration_fee": "49000", "other_costs": "10000",
        })
        acquisition = Acquisition.objects.get(submission=sub)
        self.assertEqual(acquisition.total_cost, Decimal("5302000"))
        self.client.post(reverse("dashboard:publish_listing", args=[acquisition.pk]))
        listing = Listing.objects.get(acquisition=acquisition)
        self.assertGreater(listing.price, acquisition.total_cost)

        # Buyer sends an inquiry
        self.client.logout()
        r = self.client.post(reverse("listings:inquiry", args=[listing.slug]), {"name": "Buyer", "phone": "9811111111"},
                             HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertTrue(r.json()["ok"])
        self.assertEqual(listing.inquiries.count(), 1)
        self.assertContains(self.client.get(listing.get_absolute_url()), listing.title)
