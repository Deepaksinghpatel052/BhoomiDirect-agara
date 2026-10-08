"""
python manage.py minify_assets

Writes *.min.css / *.min.js next to the source files in static/. With
USE_MINIFIED_ASSETS = True (the default when DEBUG is off) templates load the
minified files via the {% asset %} tag. Dependency-free and deliberately
conservative: strips comments and extra whitespace only.
"""
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


def minify_css(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*([{}:;,>])\s*", r"\1", text)
    return text.replace(";}", "}").strip()


def minify_js(text):
    out = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        out.append(stripped)
    text = "\n".join(out)
    return re.sub(r"/\*(?!!).*?\*/", "", text, flags=re.S)


class Command(BaseCommand):
    help = "Minify custom CSS and JS in static/ (creates .min files)."

    def handle(self, *args, **options):
        root = Path(settings.BASE_DIR) / "static"
        for path in list(root.glob("css/*.css")) + list(root.glob("js/*.js")):
            if ".min." in path.name:
                continue
            source = path.read_text(encoding="utf-8")
            result = minify_css(source) if path.suffix == ".css" else minify_js(source)
            target = path.with_name(f"{path.stem}.min{path.suffix}")
            target.write_text(result, encoding="utf-8")
            self.stdout.write(f"{path.relative_to(root)}: {len(source):,} -> {len(result):,} bytes")
        self.stdout.write(self.style.SUCCESS("Assets minified."))
