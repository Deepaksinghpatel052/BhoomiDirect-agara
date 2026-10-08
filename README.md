# BhoomiDirect Agra: Land Acquisition Platform (Demo)

A Django demo for a direct land-buying company in Agra, Uttar Pradesh. Owners submit plots, land or farms, the company evaluates and buys them directly, then resells through its partner network and its own listings.

> Brand name is set in one place: `SITE_NAME` in `agra_realestate/settings.py`.

## Contents

1. [Tech stack](#tech-stack)
2. [Run locally (without Docker)](#1-run-locally-without-docker)
3. [Run locally with Docker](#2-run-locally-with-docker)
4. [Deploy on a server (Ubuntu + Docker)](#3-deploy-on-a-server-ubuntu--docker)
5. [HTTPS with a domain](#4-https-with-a-domain)
6. [Day-to-day server commands](#5-day-to-day-server-commands)
7. [Environment variables](#environment-variables)

## Tech stack

- Python 3.11+ (tested on 3.13 / 3.14), Django 5.2, SQLite
- Django templates + Bootstrap 5, jQuery, jQuery UI (Kanban), Leaflet + OpenStreetMap, Chart.js, Bootstrap Icons
- Pillow (uploads), Gunicorn + WhiteNoise (production), Nginx (Docker)

---

## 1. Run locally (without Docker)

Requirements: Python 3.11+ and Git.

**Windows (PowerShell)**

```powershell
git clone https://github.com/Deepaksinghpatel052/BhoomiDirect-agara.git
cd BhoomiDirect-agara
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

**macOS / Linux**

```bash
git clone https://github.com/Deepaksinghpatel052/BhoomiDirect-agara.git
cd BhoomiDirect-agara
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open http://127.0.0.1:8000 (Hindi preview: http://127.0.0.1:8000/?lang=hi)

Useful local commands:

| Command | What it does |
|---|---|
| `python manage.py seed_demo` | **Wipes and reloads** all demo data (reset before a presentation) |
| `python manage.py test` | Runs the 44 automated tests |
| `python manage.py minify_assets` | Builds `*.min.css` / `*.min.js` (used when `DEBUG` is off) |
| `python manage.py fetch_photos` | Re-downloads the real demo photos (already in the repo) |
| `python manage.py createsuperuser` | Creates an extra admin user |

Local development needs no `.env`. The defaults are `DEBUG=True` and a SQLite file `db.sqlite3` in the project folder.

### Real photos

The demo uses 79 real, freely licensed photographs of farmland, plots, roads, expressways, village houses and markets in Uttar Pradesh / India from Wikimedia Commons. They are included in `static/img/photos/`, so seeding works offline. They are CC BY / CC BY-SA and require attribution: see `/photo-credits/` (linked in the footer) and `docs/PHOTO_CREDITS.md`. Replace them with the company's own property photos before going live.

---

## 2. Run locally with Docker

Requirements: [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose).

```bash
cp .env.example .env            # Windows PowerShell: copy .env.example .env
# Edit .env. For local use set:
#   DJANGO_SECRET_KEY=<any long random text>
#   HTTP_PORT=8080
#   DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
#   SITE_DOMAIN=http://localhost:8080
docker compose up -d --build
```

Open http://localhost:8080 (or the `HTTP_PORT` you chose).

What happens on start (`docker/entrypoint.sh`):

1. Database migrations are applied.
2. On the **first** start (empty database), the demo data and real photos are loaded automatically (`SEED_DEMO_ON_START=true`). Later restarts keep your data.
3. Gunicorn starts and Nginx serves the site on `HTTP_PORT`.

Everything the site needs is inside the image or the data volume:

| Item | Where it lives |
|---|---|
| CSS, JS, icons, logo, real photos, Django admin styles | Built into the image (`collectstatic` at build time), served by WhiteNoise |
| SQLite database `db.sqlite3` | Docker volume `app_data` → `/app/data` |
| Uploaded / demo property photos | `app_data` volume → `/app/data/media` (served by Nginx) |
| Private title documents | `app_data` volume → `/app/data/private_media` (never public) |

---

## 3. Deploy on a server (Ubuntu + Docker)

Works on Ubuntu 22.04 / 24.04. 1 vCPU and 1-2 GB RAM is enough for the demo.

**Step 1: Install Docker** (once per server)

```bash
sudo apt update && sudo apt install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER      # then log out and log back in
docker --version && docker compose version
```

**Step 2: Get the code**

```bash
cd /opt
sudo git clone https://github.com/Deepaksinghpatel052/BhoomiDirect-agara.git bhoomidirect
sudo chown -R $USER:$USER /opt/bhoomidirect
cd /opt/bhoomidirect
```

**Step 3: Create `.env`**

```bash
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(50))"   # copy the output as DJANGO_SECRET_KEY
nano .env
```

Set at least:

```ini
DJANGO_SECRET_KEY=<the random string>
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=<server-ip>,your-domain.com,www.your-domain.com
DJANGO_CSRF_TRUSTED_ORIGINS=http://<server-ip>,https://your-domain.com,https://www.your-domain.com
SITE_DOMAIN=https://your-domain.com          # or http://<server-ip> if there is no domain yet
DJANGO_ADMIN_PASSWORD=<a strong password>    # replaces the demo password admin123
HTTP_PORT=80
```

**Step 4: Start**

```bash
docker compose up -d --build
docker compose ps                  # web should show "healthy"
docker compose logs -f web         # watch start-up (Ctrl+C stops watching, not the app)
```

Open `http://<server-ip>/`. The admin panel is at `/admin/` and the staff dashboard is at `/dashboard/`.

**Step 5: Firewall** (if UFW is enabled)

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 4. HTTPS with a domain

Point the domain's **A record** to the server IP, then pick one option.

**Option A: Cloudflare (easiest).** Add the domain to Cloudflare, turn on the orange-cloud proxy and set SSL mode to *Flexible* (or *Full* if you also do Option B). Keep `HTTP_PORT=80`.

**Option B: Certbot on the server.** Run the app on an internal port and let the host's Nginx handle HTTPS.

1. In `.env` set `HTTP_PORT=8080`, then run `docker compose up -d`.
2. Install Nginx and Certbot: `sudo apt install -y nginx certbot python3-certbot-nginx`
3. Create `/etc/nginx/sites-available/bhoomidirect` with:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    client_max_body_size 30M;
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

4. Enable it and get a certificate:

```bash
sudo ln -s /etc/nginx/sites-available/bhoomidirect /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

5. Once HTTPS works, harden `.env` and restart with `docker compose up -d`:

```ini
DJANGO_SECURE_SSL_REDIRECT=true
DJANGO_SECURE_COOKIES=true
DJANGO_HSTS_SECONDS=31536000
```

---

## 5. Day-to-day server commands

```bash
cd /opt/bhoomidirect

# Update to the latest code
git pull
docker compose up -d --build

# Status and logs
docker compose ps
docker compose logs -f web
docker compose logs -f nginx

# Restart / stop
docker compose restart
docker compose down                     # keeps the database volume

# Django commands inside the container
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_demo      # RESETS all demo data
docker compose exec web python manage.py test

# Back up the database and uploads
docker compose exec web sh -c "cd /app && tar czf - data" > backup-$(date +%F).tar.gz

# Restore a backup (volume name: see `docker volume ls`)
docker compose down
docker run --rm -v bhoomidirect_app_data:/app/data -v "$PWD":/backup alpine \
  sh -c "cd /app && tar xzf /backup/backup-YYYY-MM-DD.tar.gz"
docker compose up -d

# Start completely fresh (DELETES the database and uploads)
docker compose down -v && docker compose up -d --build
```

> The volume is named `<folder-name>_app_data` (for example `bhoomidirect_app_data`).

---

## Environment variables

All settings come from `.env` (see `.env.example`). The defaults are safe for local development.

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | demo key | **Must** be a random value on a server |
| `DJANGO_DEBUG` | `True` | Use `false` on a server |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost,*` | Domains / IPs the site answers on |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | empty | Full origins (`https://domain.com`) allowed to submit forms |
| `SITE_DOMAIN` | `http://127.0.0.1:8000` | Used in canonical URLs, sitemap and social tags |
| `SEED_DEMO_ON_START` | `true` | Docker: load demo data on the first start only |
| `DJANGO_ADMIN_USERNAME` / `DJANGO_ADMIN_PASSWORD` | `admin` / empty | Docker: sets the admin password on every start |
| `HTTP_PORT` | `80` | Public port of the Nginx container |
| `GUNICORN_WORKERS` / `GUNICORN_TIMEOUT` | `3` / `60` | App server tuning |
| `DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_SECURE_COOKIES`, `DJANGO_HSTS_SECONDS` | off | Turn on after HTTPS works |
| `DJANGO_SERVE_MEDIA` | `true` | Django serves `/media/` when running without Nginx |
| `DJANGO_DATA_DIR` | project folder (`/app/data` in Docker) | Location of the database and uploads |
| `DJANGO_LOG_LEVEL` | `INFO` | Log level (logs appear in `docker compose logs`) |

## Demo logins

| Role | Username | Password | Lands on |
|---|---|---|---|
| Admin (superuser) | `admin` | `admin123` | `/dashboard/`, `/admin/` |
| Evaluator | `evaluator` | `demo123` | `/dashboard/` |
| Field agent | `agent` | `demo123` | `/dashboard/` (own site visits) |
| Owner | `owner` | `demo123` | `/my/` (has an open offer to respond to) |
| Channel partner | `partner` | `demo123` | `/partner/` |

You can also log in with a mobile number or email (e.g. owner: `9876543210`).

## Key URLs

| Page | URL |
|---|---|
| Home | `/` |
| Sell your property (5-step form) | `/sell-your-property/` |
| Instant price estimator | `/price-estimator/` |
| Track submission | `/track-submission/` |
| Buy property (AJAX filters) | `/buy-property-in-agra/` |
| Locality landing page | `/sell-land-in-agra/fatehabad-road/` |
| Type landing pages | `/sell-plot-agra/`, `/sell-agricultural-land-agra/`, `/sell-commercial-land-agra/` |
| Channel partners | `/channel-partners/` |
| Blog | `/blog/` |
| Owner portal | `/my/` |
| Staff dashboard | `/dashboard/` (pipeline: `/dashboard/pipeline/`) |
| Django admin | `/admin/` |
| SEO | `/sitemap.xml`, `/robots.txt` |

## Features

**Public site (owner-first)**
- Hero quick-lead form that creates a `New` submission, then pre-fills the full form
- 5-step sell form: progress bar, session-saved steps (go back without losing data), Leaflet map pin picker, tehsil-to-locality filtering, live unit converter (sq ft, gaj, sq m, biswa, bigha, acre, hectare), conditional agricultural and legal fields, drag-and-drop photo upload with preview, size/type checks, Indian mobile validation, mock OTP (marked DEMO)
- Thank-you page with reference ID (`BDA-2026-00042` format), WhatsApp share and tracking link
- Price estimator (sample circle rate × area × market multiplier) with AJAX and a clear disclaimer
- Vertical status timeline for tracking
- Listings with AJAX filtering, grid/list toggle and pagination; detail page with gallery, specs, map, inquiry form, WhatsApp/call
- SEO landing pages per locality and property type, blog, FAQ, About, Contact (map), Privacy, Terms, custom 403/404/500
- Floating WhatsApp button, mobile call/sell bar, EN / हिंदी toggle (placeholder) on hero and main CTAs

**Owner portal**: signup/login by phone or email, submissions with status badges, timeline, site visit date, accept / reject / counter offers, upload more photos and documents, in-app notifications.

**Staff dashboard** (role-based):
- Overview KPIs and Chart.js charts (weekly leads, locality, type, funnel)
- Drag-and-drop Kanban pipeline (jQuery UI) that saves status by AJAX and writes `StatusHistory`
- Leads table with search, filters and CSV export
- Lead detail: data, photos, private documents, map, call/WhatsApp, assign agent, schedule visits, visit report, live evaluation scorecard (Strong Buy / Consider / Reject, circle-rate value, resale value, margin %), legal checklist with progress bar, offers, acquisition, notes, activity log
- Acquired properties with one-click "Publish for Resale"; inventory with booked/sold and profit; buyer inquiries; partner approval; localities and sample circle rate management

**Permissions**
| Action | Admin | Evaluator | Field agent |
|---|---|---|---|
| View dashboard, pipeline, notes, visits | ✓ | ✓ | ✓ (visits: own only) |
| Evaluation, legal, offers, CSV export | ✓ | ✓ | ✗ |
| Record acquisition, publish, edit listings, approve partners, edit rates | ✓ | ✗ | ✗ |

Owners can see only their own submissions. Title documents are stored in `private_media/` (outside `MEDIA_ROOT`) and served only to staff or the property's owner.

**SEO**: per-page title, meta description, canonical, Open Graph and Twitter tags; `sitemap.xml` (static pages, localities, listings, blog); `robots.txt`; JSON-LD for `RealEstateAgent`/`LocalBusiness`, `FAQPage`, `BreadcrumbList`, `Product`/`Offer`, `Article`; breadcrumbs; one H1 per page; lazy images with alt text; deferred scripts. See `docs/SEO_STRATEGY.md`.

## Configuration

In `agra_realestate/settings.py`:
- `SITE_NAME`, `SITE_TAGLINE`, phone / WhatsApp / address
- `AREA_BIGHA_SQ_METER` (default 2529.29 sq m, the Agra "pucca bigha") and `AREA_BISWA_PER_BIGHA` (20). Bigha size varies by region, so change it here if needed.
- `ESTIMATOR_MARKET_MULTIPLIER_LOW/HIGH`
- Environment variables: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `SITE_DOMAIN`, `USE_MINIFIED_ASSETS`

**All circle rates in this demo are sample values, not official rates.**

## Tests

```powershell
python manage.py test
```

44 tests cover: reference ID generation, area unit conversion, evaluation scoring, the full sell form (including OTP and uploads), file validation, permissions, private documents, partner flows, and an end-to-end flow from submission through offer, acquisition, listing and buyer inquiry.

## Project structure

```
agra_realestate/   settings, urls
core/              home & static pages, SEO helpers, template tags, seed_demo / minify_assets commands
accounts/          custom User (roles, phone), phone/email login, notifications
locations/         tehsils, localities, sample circle rates, unit conversion, estimator, landing pages
submissions/       owner submissions, multi-step form, tracking, owner portal, status service
acquisitions/      site visits, evaluation, legal checklist, offers, acquisitions, activity log, staff dashboard
listings/          resale listings, buyer inquiries
partners/          channel partner registration and portal
blog/              SEO articles
templates/         base.html, partials/, one folder per app, dashboard/
static/            css/, js/, img/
docs/              SEO strategy, demo walkthrough, future scope, photo credits
docker/            entrypoint.sh (migrate + first-run seed), nginx/default.conf
Dockerfile         production image (Gunicorn + WhiteNoise, static files built in)
docker-compose.yml web + nginx services, persistent app_data volume
.env.example       all server settings
```
