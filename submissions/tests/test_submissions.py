import io
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from accounts.models import User
from core.tests.helpers import make_locality, make_submission, make_user
from submissions.constants import Status
from submissions.forms import QuickLeadForm, Step1OwnerForm, Step4LegalForm
from submissions.models import PropertySubmission, StatusHistory
from submissions.services import change_status


def png_file(name="photo.png"):
    buf = io.BytesIO()
    Image.new("RGB", (20, 20), "green").save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


class ReferenceIdTests(TestCase):
    def test_reference_id_format(self):
        loc = make_locality()
        sub = make_submission(loc)
        self.assertEqual(sub.reference_id, f"BDA-{timezone.now().year}-{sub.pk:05d}")
        self.assertRegex(sub.reference_id, r"^BDA-\d{4}-\d{5}$")

    def test_reference_id_is_unique_and_stable(self):
        loc = make_locality()
        a, b = make_submission(loc), make_submission(loc)
        self.assertNotEqual(a.reference_id, b.reference_id)
        original = a.reference_id
        a.owner_name = "Changed"
        a.save()
        self.assertEqual(a.reference_id, original)

    def test_area_normalised_on_save(self):
        loc = make_locality()
        sub = make_submission(loc, area_value=Decimal("2"), area_unit="bigha")
        self.assertEqual(sub.area_sq_meter, Decimal("5058.57"))


class FormValidationTests(TestCase):
    def test_indian_phone_validation(self):
        for phone, ok in (("9876543210", True), ("6123456789", True), ("5876543210", False), ("98765", False), ("98765432101", False)):
            with self.subTest(phone=phone):
                form = QuickLeadForm({"owner_name": "A", "phone": phone, "property_type": "residential_plot"})
                self.assertEqual(form.is_valid(), ok)

    def test_step1_requires_name_and_phone(self):
        form = Step1OwnerForm({"relation": "owner"})
        self.assertFalse(form.is_valid())
        self.assertIn("owner_name", form.errors)
        self.assertIn("phone", form.errors)

    def test_legal_step_requires_details_when_loan(self):
        base = {"ownership_type": "single", "number_of_owners": 1, "mutation_done": "yes", "approval_status": "ada"}
        self.assertTrue(Step4LegalForm(base).is_valid())
        form = Step4LegalForm({**base, "has_loan": "on"})
        self.assertFalse(form.is_valid())
        self.assertIn("encumbrance_details", form.errors)

    def test_joint_ownership_needs_two_owners(self):
        form = Step4LegalForm({"ownership_type": "joint", "number_of_owners": 1, "mutation_done": "yes", "approval_status": "ada"})
        self.assertFalse(form.is_valid())


@override_settings(MEDIA_ROOT="test_media_tmp", PRIVATE_MEDIA_ROOT="test_private_tmp")
class SellWizardFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.loc = make_locality()

    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree("test_media_tmp", ignore_errors=True)
        shutil.rmtree("test_private_tmp", ignore_errors=True)
        super().tearDownClass()

    def step(self, n):
        return reverse("submissions:sell_step", args=[n])

    def test_full_wizard_creates_submission(self):
        c = self.client
        r = c.post(self.step(1), {"owner_name": "Sita Ram", "phone": "9123456780", "relation": "owner"})
        self.assertRedirects(r, reverse("submissions:sell_verify"))
        c.get(reverse("submissions:sell_verify"))
        otp = c.session["sell_otp"]
        r = c.post(reverse("submissions:sell_verify"), {"otp": "0000" if otp != "0000" else "1111"})
        self.assertEqual(r.status_code, 200)  # wrong OTP
        r = c.post(reverse("submissions:sell_verify"), {"otp": otp})
        self.assertRedirects(r, self.step(2))

        r = c.post(self.step(2), {"property_type": "agricultural_land", "tehsil": self.loc.tehsil_id, "locality": self.loc.pk})
        self.assertRedirects(r, self.step(3))
        # Back navigation keeps data
        self.assertContains(c.get(self.step(2)), "agricultural_land")
        r = c.post(self.step(3), {"area_value": "3", "area_unit": "bigha", "irrigation_source": "tubewell"})
        self.assertRedirects(r, self.step(4))
        r = c.post(self.step(4), {"ownership_type": "single", "number_of_owners": 1, "title_documents": ["khatauni", "registry"],
                                  "mutation_done": "yes", "approval_status": "na"})
        self.assertRedirects(r, self.step(5))
        r = c.post(self.step(5), {"expected_price": "4500000", "urgency": "1_month", "consent": "on",
                                  "photos": [png_file("a.png"), png_file("b.png")]})
        sub = PropertySubmission.objects.get(phone="9123456780")
        self.assertRedirects(r, reverse("submissions:thank_you", args=[sub.reference_id]))
        self.assertTrue(sub.is_complete)
        self.assertTrue(sub.phone_verified)
        self.assertEqual(sub.photos.count(), 2)
        self.assertEqual(sub.title_documents, ["khatauni", "registry"])
        self.assertEqual(sub.irrigation_source, "tubewell")
        self.assertEqual(sub.area_sq_meter, Decimal("7587.86"))
        self.assertTrue(StatusHistory.objects.filter(submission=sub, new_status=Status.NEW).exists())

    def test_cannot_skip_steps(self):
        self.assertRedirects(self.client.get(self.step(4)), self.step(1))

    def test_rejects_non_image_upload(self):
        session_steps = {
            "1": {"owner_name": ["X"], "phone": ["9123456781"], "relation": ["owner"]},
            "2": {"property_type": ["residential_plot"], "tehsil": [str(self.loc.tehsil_id)], "locality": [str(self.loc.pk)]},
            "3": {"area_value": ["100"], "area_unit": ["sqyard"]},
            "4": {"ownership_type": ["single"], "number_of_owners": ["1"], "mutation_done": ["yes"], "approval_status": ["ada"]},
        }
        session = self.client.session
        session["sell_wizard"] = session_steps
        session["sell_verified_phone"] = "9123456781"
        session.save()
        bad = SimpleUploadedFile("virus.exe", b"MZ...", content_type="application/octet-stream")
        r = self.client.post(self.step(5), {"expected_price": "100000", "urgency": "exploring", "consent": "on", "photos": [bad]})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(PropertySubmission.objects.filter(phone="9123456781").exists())

    def test_quick_lead_creates_new_submission(self):
        r = self.client.post(reverse("submissions:quick_lead"), {"owner_name": "Quick", "phone": "9000000001", "property_type": "commercial_plot", "locality": self.loc.pk})
        self.assertRedirects(r, self.step(1))
        sub = PropertySubmission.objects.get(phone="9000000001")
        self.assertEqual(sub.status, Status.NEW)
        self.assertFalse(sub.is_complete)

    def test_track_submission(self):
        sub = make_submission(self.loc)
        r = self.client.get(reverse("submissions:track"), {"reference_id": sub.reference_id, "phone": sub.phone})
        self.assertContains(r, sub.reference_id)
        self.assertContains(r, "Current")
        r = self.client.get(reverse("submissions:track"), {"reference_id": sub.reference_id, "phone": "9999999999"})
        self.assertContains(r, "No submission found")


class StatusServiceTests(TestCase):
    def test_change_status_writes_history_and_notifies(self):
        loc = make_locality()
        owner = make_user("o", User.Role.OWNER, "9876500009")
        sub = make_submission(loc, owner_user=owner)
        self.assertTrue(change_status(sub, Status.CONTACTED, None, "Called"))
        self.assertFalse(change_status(sub, Status.CONTACTED))
        self.assertEqual(sub.status_history.count(), 1)
        self.assertEqual(owner.notifications.count(), 1)
        self.assertEqual(sub.activities.count(), 1)
