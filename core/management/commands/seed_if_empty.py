"""Load demo data only when the database has no users (safe to run on every start)."""
from django.core.management import call_command
from django.core.management.base import BaseCommand

from accounts.models import User


class Command(BaseCommand):
    help = "Run seed_demo only if the database is empty (used by the Docker entrypoint)."

    def handle(self, *args, **options):
        if User.objects.exists():
            self.stdout.write("Database already has data: skipping demo seed.")
            return
        self.stdout.write("Empty database: loading demo data...")
        call_command("seed_demo")
