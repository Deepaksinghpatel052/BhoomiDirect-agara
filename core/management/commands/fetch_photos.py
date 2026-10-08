"""
python manage.py fetch_photos

Downloads the curated set of real, freely licensed photographs (Wikimedia
Commons, CC BY / CC BY-SA) listed in _photo_library.json into
static/img/photos/<theme>-NN.jpg and writes attribution to
static/img/photos/credits.json and docs/PHOTO_CREDITS.md.

Run once (needs internet). `seed_demo` then uses these photos offline and
falls back to generated placeholders only if the folder is empty.
"""
import io
import json
import time
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from PIL import Image

API = "https://commons.wikimedia.org/w/api.php?"
HEADERS = {"User-Agent": "BhoomiDirectAgraDemo/1.0 (demo photo seeding)"}
LIBRARY = Path(__file__).with_name("_photo_library.json")
WIDTH = 1200


def fetch(url, attempts=6):
    """GET with polite exponential backoff on HTTP 429 / 5xx."""
    delay = 3
    for attempt in range(attempts):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60).read()
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == attempts - 1:
                raise
            retry_after = exc.headers.get("Retry-After")
            time.sleep(int(retry_after) if retry_after and retry_after.isdigit() else delay)
            delay *= 2


def photo_dir():
    return Path(settings.BASE_DIR) / "static" / "img" / "photos"


class Command(BaseCommand):
    help = "Download the curated real photo library from Wikimedia Commons."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Re-download files that already exist")

    def handle(self, *args, **options):
        out = photo_dir()
        out.mkdir(parents=True, exist_ok=True)
        library = json.loads(LIBRARY.read_text(encoding="utf-8"))
        counters, credits = {}, []
        for theme, title, license_name, artist in library:
            counters[theme] = counters.get(theme, 0) + 1
            name = f"{theme}-{counters[theme]:02d}.jpg"
            target = out / name
            try:
                time.sleep(0.2)
                info = self.lookup(title)
            except Exception as exc:
                self.stderr.write(f"Lookup failed {title}: {exc}")
                continue
            if info is None:
                self.stderr.write(f"Skipped (not found): {title}")
                continue
            if options["force"] or not target.exists():
                try:
                    self.download(info["thumburl"], target)
                except Exception as exc:  # network or decode error: keep going
                    self.stderr.write(f"Failed {title}: {exc}")
                    continue
                time.sleep(1.0)
            credits.append({
                "file": name, "theme": theme, "title": title, "artist": artist,
                "license": license_name, "source": info["descriptionurl"],
            })
            self.stdout.write(f"{name}  <- {title}")

        (out / "credits.json").write_text(json.dumps(credits, ensure_ascii=False, indent=1), encoding="utf-8")
        self.write_credits_md(credits)
        self.stdout.write(self.style.SUCCESS(f"{len(credits)} photos ready in {out}"))

    def lookup(self, title):
        params = {
            "action": "query", "format": "json", "titles": f"File:{title}", "prop": "imageinfo",
            "iiprop": "url", "iiurlwidth": WIDTH + 80,
        }
        data = json.loads(fetch(API + urllib.parse.urlencode(params)))
        for page in data["query"]["pages"].values():
            if "imageinfo" in page:
                return page["imageinfo"][0]
        return None

    def download(self, url, target):
        raw = fetch(url)
        # Re-encode through Pillow: validates the image and strips metadata.
        img = Image.open(io.BytesIO(raw))
        img.load()
        img = img.convert("RGB")
        if img.width > WIDTH:
            img = img.resize((WIDTH, round(img.height * WIDTH / img.width)), Image.LANCZOS)
        img.save(target, "JPEG", quality=82, optimize=True, progressive=True)

    def write_credits_md(self, credits):
        lines = [
            "# Photo Credits",
            "",
            "Real photographs used in the demo come from Wikimedia Commons under free licenses.",
            "CC BY / CC BY-SA require attribution: keep this file (it is also linked in the site footer).",
            "Before going live, replace them with the company's own property photos.",
            "",
            "| File | Photo | Author | License |",
            "|---|---|---|---|",
        ]
        for c in credits:
            artist = (c["artist"] or "Unknown").replace("|", "/")
            lines.append(f"| {c['file']} | [{c['title']}]({c['source']}) | {artist} | {c['license']} |")
        path = Path(settings.BASE_DIR) / "docs" / "PHOTO_CREDITS.md"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
