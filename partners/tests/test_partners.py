from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from core.tests.helpers import make_locality
from partners.models import ChannelPartner
from submissions.models import PropertySubmission


class PartnerTests(TestCase):
    def test_registration_creates_pending_partner_with_login(self):
        loc = make_locality()
        r = self.client.post(reverse("partners:join"), {
            "name": "Test Broker", "phone": "9822233344", "password": "secret123", "experience_years": 3,
            "areas_covered": [loc.pk],
        })
        self.assertEqual(r.status_code, 302)
        partner = ChannelPartner.objects.get(phone="9822233344")
        self.assertFalse(partner.is_approved)
        self.assertEqual(partner.user.role, User.Role.CHANNEL_PARTNER)
        self.assertTrue(self.client.login(username="9822233344", password="secret123"))

    def test_unapproved_partner_cannot_refer(self):
        loc = make_locality()
        user = User.objects.create_user("p", password="x12345", role=User.Role.CHANNEL_PARTNER, phone="9822233355")
        partner = ChannelPartner.objects.create(user=user, name="P", phone="9822233355")
        self.client.force_login(user)
        data = {"owner_name": "Owner", "phone": "9876511111", "property_type": "agricultural_land", "locality": loc.pk}
        self.client.post(reverse("partners:refer_owner"), data)
        self.assertFalse(PropertySubmission.objects.exists())
        partner.is_approved = True
        partner.save()
        self.client.post(reverse("partners:refer_owner"), data)
        sub = PropertySubmission.objects.get()
        self.assertEqual(sub.source, "partner")
        self.assertEqual(sub.referred_by, partner)

    def test_portal_requires_partner_role(self):
        owner = User.objects.create_user("o", password="x12345", role=User.Role.OWNER, phone="9822233366")
        self.client.force_login(owner)
        self.assertEqual(self.client.get(reverse("partners:portal")).status_code, 403)
