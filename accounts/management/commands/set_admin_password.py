"""Set the admin password from DJANGO_ADMIN_PASSWORD (used by the Docker entrypoint)."""
import os

from django.core.management.base import BaseCommand

from accounts.models import User


class Command(BaseCommand):
    help = "Set the password of DJANGO_ADMIN_USERNAME (default 'admin') from DJANGO_ADMIN_PASSWORD."

    def handle(self, *args, **options):
        password = os.environ.get("DJANGO_ADMIN_PASSWORD", "")
        username = os.environ.get("DJANGO_ADMIN_USERNAME", "admin")
        if not password:
            self.stdout.write("DJANGO_ADMIN_PASSWORD not set: nothing to do.")
            return
        user = User.objects.filter(username=username).first()
        if user is None:
            user = User.objects.create_superuser(username=username, email="", password=password, role=User.Role.ADMIN)
            self.stdout.write(self.style.SUCCESS(f"Created superuser '{username}'."))
            return
        user.set_password(password)
        user.save(update_fields=["password"])
        self.stdout.write(self.style.SUCCESS(f"Password updated for '{username}'."))
