from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from core.tests.helpers import make_locality, make_submission


class AuthTests(TestCase):
    def test_login_with_phone_email_or_username(self):
        User.objects.create_user("ramesh", email="r@example.com", password="pass1234", phone="9876512345")
        for identifier in ("ramesh", "r@example.com", "9876512345", "+919876512345"):
            with self.subTest(identifier=identifier):
                self.assertTrue(self.client.login(username=identifier, password="pass1234"))
                self.client.logout()

    def test_signup_links_existing_submissions(self):
        sub = make_submission(make_locality(), phone="9876598765")
        r = self.client.post(reverse("accounts:signup"), {
            "first_name": "Owner", "phone": "9876598765", "password1": "strongpass1", "password2": "strongpass1",
        })
        self.assertRedirects(r, reverse("submissions:owner_dashboard"))
        sub.refresh_from_db()
        self.assertEqual(sub.owner_user.phone, "9876598765")

    def test_role_redirect_after_login(self):
        staff = User.objects.create_user("e", password="pass1234", role=User.Role.EVALUATOR, phone="9876500000")
        self.client.force_login(staff)
        self.assertRedirects(self.client.get(reverse("accounts:after_login")), reverse("dashboard:overview"))
