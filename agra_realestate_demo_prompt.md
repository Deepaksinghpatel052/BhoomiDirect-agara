# Prompt for Claude Code: Agra Land Acquisition Platform (Django Demo)

Copy everything below this line into Claude Code.

---

You are a senior Django developer and real estate product designer. Build a **fully working demo website** for a real estate company in **Agra, Uttar Pradesh, India**. I will use this demo to pitch a client, so it must look professional, run locally without errors, and come with realistic sample data.

## 1. Client's business (read carefully, every feature must serve this)

The company is NOT a normal listing portal. Its model is:

1. **Acquisition (main focus):** Direct property owners in and around Agra submit details of plots, land, or agricultural property they want to sell.
2. **Evaluation:** The company's team reviews each submission (location, legal status, price, demand) and decides whether to buy.
3. **Direct purchase:** The company makes an offer and buys suitable properties directly from owners (no brokers in between).
4. **Resale:** Acquired properties are resold through the company's own network (brokers/channel partners) and digital channels (its own listings).
5. **SEO:** The site must rank on Google for searches like "sell my land in Agra", "sell plot Agra", "sell agricultural land Agra", "plot for sale Fatehabad Road".

The website should therefore be **owner-first**: the biggest call to action everywhere is "Sell Your Property to Us".

Brand name for the demo: **"BhoomiDirect Agra"** (keep it in one settings variable `SITE_NAME` so I can change it easily). Tagline: "Sell your land directly. Fair price. Fast payment. No brokers."

## 2. Tech stack (strict)

- **Backend:** Python 3.11+, Django 5.x
- **Database:** Django default SQLite
- **Frontend:** Django templates with HTML5, CSS3, **Bootstrap 5**, JavaScript, **jQuery** (no React/Vue/Tailwind)
- **Maps:** Leaflet.js with OpenStreetMap tiles (free, no API key)
- **Charts:** Chart.js
- **Icons:** Bootstrap Icons
- **Images:** Pillow for uploads
- Keep third-party Python packages minimal. Allowed: `Pillow`, `django-environ` (optional). Use Django's built-in sitemap framework, auth, messages, and admin.
- All CDN links (Bootstrap, jQuery, Leaflet, Chart.js) loaded in `base.html`.
- Must be fully responsive (mobile first, since most Agra owners will use phones).

## 3. Project structure

Project name: `agra_realestate`. Create these apps:

| App | Purpose |
|---|---|
| `core` | Home, about, how it works, contact, FAQ, static pages, site settings |
| `accounts` | Custom user model (phone + email), roles: Owner, Field Agent, Evaluator, Admin, Channel Partner, Buyer |
| `submissions` | Owner property submission (multi-step form), documents, photos, tracking |
| `acquisitions` | Internal pipeline: leads, site visits, evaluation scorecard, legal checklist, offers, purchase |
| `listings` | Resale inventory (acquired properties published for buyers), buyer inquiries |
| `partners` | Channel partner / broker network registration and lead sharing |
| `locations` | Agra areas, tehsils, localities, sample circle rates, SEO landing pages |
| `blog` | SEO articles (guides for land sellers) |

Use a custom user model from the start (`AUTH_USER_MODEL = "accounts.User"`). Use `templates/` and `static/` folders at project root, with a clean `base.html`, `partials/` (navbar, footer, messages, pagination) and separate templates per app.

## 4. Data models (minimum)

**locations**
- `Tehsil` (Agra Sadar, Etmadpur, Kiraoli, Kheragarh, Fatehabad, Bah, Fatehpur Sikri)
- `Locality` (name, slug, tehsil FK, type: urban colony / highway belt / village, lat, lng, description, is_featured, SEO fields)
  Seed with real Agra areas: Fatehabad Road, Shamshabad Road, Sikandra, Kamla Nagar, Dayalbagh, Shastripuram, Tajganj, Kalindi Vihar, Agra-Lucknow Expressway belt, Yamuna Expressway belt, Gwalior Road, Runkata, Etmadpur, Kiraoli, Fatehpur Sikri, Bichpuri, Artoni, Kheragarh.
- `CircleRate` (locality FK, property_type, rate_per_sq_meter, effective_year). **Label clearly in the UI as "Sample rates for demo, not official"**.

**submissions**
- `PropertySubmission`:
  - `reference_id` auto-generated like `BDA-2026-00042`
  - Owner info: name, phone, WhatsApp number, email, relation to property (owner / co-owner / power of attorney holder / family member)
  - Property type: Residential Plot, Commercial Plot, Agricultural Land, Farmhouse Land, Industrial Land, Plot with Old Construction
  - Location: tehsil, locality, village/colony name, khasra/gata number (optional), landmark, full address, latitude, longitude (from map pin)
  - Size: area value + unit. Support Indian units: **sq ft, sq yard (gaj), sq meter, biswa, bigha, acre, hectare**. Store a normalized `area_sq_meter` field computed on save. Note in code that bigha/biswa sizes vary by region and use an Agra/UP common value as a configurable constant.
  - Plot details: road width (ft), frontage (ft), facing direction, corner plot (yes/no), boundary wall, electricity, water source, distance from main road
  - Agricultural details (show only if agricultural): irrigation source, current crop, soil type, tubewell/borewell
  - Legal: ownership type (single/joint), number of owners, title document available (Registry/Sale Deed, Khatauni, GPA, Will, Other), mutation (dakhil kharij) done, ADA approved / RERA status, any loan on property, any court dispute, encumbrance details
  - Commercial: expected price, price negotiable, reason for selling, urgency (within 1 month / 1-3 months / just exploring)
  - Preferred time for site visit
  - Consent checkbox
  - Status (see pipeline), created_at, updated_at, source (website / WhatsApp / referral / partner)
- `SubmissionPhoto` (multiple images)
- `SubmissionDocument` (doc type + file; mark as "visible only to company")
- `StatusHistory` (submission, old status, new status, note, changed_by, timestamp) used for the owner timeline

**acquisitions**
- Pipeline statuses: `New` → `Contacted` → `Site Visit Scheduled` → `Site Visit Done` → `Under Evaluation` → `Legal Verification` → `Offer Made` → `Negotiation` → `Offer Accepted` → `Acquired` | `Rejected` | `Owner Withdrew`
- `SiteVisit` (submission, assigned agent, scheduled date, visit notes, photos, ground-reality checks)
- `Evaluation` scorecard with fields scored 1-10: location potential, road access, legal clarity, price vs market, resale demand, development nearby. Auto-compute total score and a recommendation: **Strong Buy / Consider / Reject**. Also show expected price vs circle rate value vs estimated resale value and estimated margin %.
- `LegalChecklist` (title verified, khatauni matched, no encumbrance, mutation verified, owner ID verified, NOC if needed) with progress bar
- `Offer` (submission, amount, valid till, terms, status: pending / accepted / rejected / countered, owner counter amount)
- `Acquisition` (final purchase price, purchase date, registry date, payment mode, total cost incl. stamp duty)
- `ActivityLog` for every action (who, what, when)

**listings**
- `Listing` created from an `Acquisition` with one click ("Publish for Resale"): title, slug, description, price, area, type, locality, photos, features, status (available / booked / sold), is_featured, SEO fields
- `BuyerInquiry` (listing, name, phone, budget, message, status)

**partners**
- `ChannelPartner` (name, firm, phone, areas covered, RERA agent number optional, approved flag)
- Partners can see available listings and refer buyers; also can refer owners (lead source = partner).

**blog**
- `Post` (title, slug, content, cover image, meta title, meta description, published date, category)

## 5. Public website pages

1. **Home**
   - Hero: headline "Sell Your Plot, Land or Farm in Agra Directly to Us", subtext, two CTAs: "Submit Your Property" (primary) and "Get Instant Price Estimate"
   - Quick lead form in hero (name, phone, property type, locality) that creates a submission with status New and redirects to complete details
   - Trust stats counters (properties acquired, acres evaluated, payout amount, average days to close), animated with jQuery
   - "How it works" 5 steps: Submit → Free Evaluation → Site Visit → Fair Offer → Registry & Payment
   - Why sell to us: no broker commission, legal help, fast payment, transparent valuation, we handle paperwork
   - Property types we buy (cards)
   - Areas we buy in (cards linking to locality landing pages) and a Leaflet map with markers
   - Recently acquired properties (proof), testimonials from owners, FAQ accordion, final CTA band
2. **Sell Your Property** multi-step form (the most important page)
   - 5 steps with a progress bar: Owner Details → Property Type & Location (Leaflet map pin picker) → Size & Features → Legal Details → Price, Photos & Documents
   - Conditional fields with jQuery (agricultural fields only for agricultural land, etc.)
   - Live **unit converter** (enter bigha and see sq ft / gaj / acre instantly)
   - Client-side validation (jQuery) plus server-side Django validation
   - Indian phone validation (10 digits, starts with 6-9)
   - Image preview before upload, drag-and-drop zone, file size/type limits
   - Mock OTP verification step (show a fake OTP in a message for demo, clearly marked as demo)
   - Save step data in session so the user can go back without losing data
   - On success: thank-you page with reference ID, WhatsApp share button, "Track your submission" link
3. **Instant Price Estimator** page: select locality + type + area → shows an indicative range based on sample circle rates and a market multiplier, with disclaimer and CTA "Get exact offer, submit your property"
4. **Track Submission**: enter reference ID + phone → shows status timeline (vertical stepper)
5. **Buy Property** listings page with filters (type, locality, budget range, area range, sort), grid/list toggle, AJAX filtering with jQuery, pagination
6. **Listing detail**: photo gallery, key specs table, map, nearby landmarks, inquiry form, WhatsApp/call buttons, similar properties
7. **Locality landing pages** (SEO): URL like `/sell-land-in-agra/fatehabad-road/` with unique heading, area description, sample circle rate, connectivity, local FAQ, CTA form, available listings in that area
8. **Property type landing pages**: `/sell-agricultural-land-agra/`, `/sell-plot-agra/`, `/sell-commercial-land-agra/`
9. **Channel Partner** page with registration form
10. **About, Contact (with map), FAQ, Blog list, Blog detail, Privacy Policy, Terms**
11. Custom **404 and 500** pages

Global elements: sticky navbar with "Sell Property" button highlighted, floating WhatsApp button, click-to-call on mobile, footer with areas served links (good for SEO), language toggle placeholder (English / हिंदी) with Hindi labels on the main CTAs and hero.

## 6. Owner portal (login required, role Owner)

- Signup/login with phone or email + password
- Dashboard: my submissions with status badges
- Submission detail: timeline, site visit date, uploaded docs, offers received
- **Respond to offers:** Accept / Reject / Counter with amount
- Add more photos or documents to an existing submission
- Notifications list (in-app, stored in DB)

## 7. Company dashboard (custom UI, not only Django admin)

Build a separate staff dashboard at `/dashboard/` with a sidebar layout (Bootstrap), role-based access:

- **Overview:** KPI cards (new leads today, under evaluation, offers pending, acquired this month, inventory value, sold), Chart.js charts (leads per week, leads by locality, leads by property type, funnel conversion by stage)
- **Leads pipeline:** Kanban board by status with drag-and-drop (jQuery UI sortable) that updates status via AJAX and writes StatusHistory; plus a table view with search and filters (locality, type, status, urgency, assigned agent, date)
- **Lead detail page:** all submission data, photos gallery, documents, map, owner contact buttons (call / WhatsApp), assign agent, schedule site visit, evaluation scorecard form with live score calculation, legal checklist with progress, create offer, activity log, internal notes
- **Site visits calendar/list** for field agents
- **Acquired properties:** mark as acquired, record purchase cost, "Publish for Resale" button creating a Listing
- **Inventory & sales:** listings, buyer inquiries, mark booked/sold, profit per property
- **Partners:** approve channel partners, see referrals
- **Circle rates & localities** management
- **CSV export** of leads

Also register all models in Django admin with good `list_display`, `list_filter`, `search_fields`.

## 8. SEO requirements (client specifically wants SEO experts, show this well)

- Clean, keyword-rich URLs with slugs
- Per-page `<title>`, meta description, canonical URL, Open Graph and Twitter tags, via a reusable template block and model SEO fields
- `sitemap.xml` (Django sitemap framework: static pages, localities, listings, blog posts) and `robots.txt`
- **Schema.org JSON-LD:** `RealEstateAgent` / `LocalBusiness` on home, `FAQPage` on FAQ and landing pages, `BreadcrumbList` on inner pages, `Offer`/`Product`-style data on listings, `Article` on blog
- Breadcrumbs on all inner pages
- Semantic HTML (one H1 per page, proper H2/H3), alt text on all images, lazy-loaded images
- Fast load: minified custom CSS/JS, defer scripts
- Seed 6 SEO blog posts with real-sounding useful content, e.g. "How to Sell Agricultural Land in Agra: Documents Checklist", "Khatauni vs Registry: What Buyers Check", "Circle Rate in Agra Explained", "Why Sell Land Directly Instead of Through a Broker", "Mutation (Dakhil Kharij) Process in UP", "Best Growing Areas for Land in Agra"
- Add a `docs/SEO_STRATEGY.md` file with target keywords, page-to-keyword mapping, and a content plan, so I can show it in the proposal

## 9. Design guidelines

- Look like a trustworthy, modern Indian property brand, not a generic template
- Color palette: deep green (land/trust) primary, warm earthy gold/terracotta accent (Agra red sandstone feel), white and light beige backgrounds; define as CSS variables in `static/css/style.css`
- Fonts from Google Fonts: Poppins for headings, Inter or Noto Sans for body (Noto Sans Devanagari for Hindi text)
- Rounded cards, soft shadows, plenty of whitespace, clear large buttons (owners may be less tech-savvy)
- Use placeholder images from Unsplash URLs or locally generated placeholder images for land, plots and fields; do not use Taj Mahal photos as the main hero (maybe a subtle skyline/illustration accent is fine)
- Status badges with consistent colors across owner portal and dashboard
- Smooth jQuery interactions: counters, form step transitions, toasts for AJAX actions

## 10. Demo data

Create a management command `python manage.py seed_demo` that creates:
- Superuser `admin / admin123`, evaluator `evaluator / demo123`, field agent `agent / demo123`, owner `owner / demo123`, channel partner `partner / demo123`
- All localities and tehsils listed above with approximate coordinates
- Sample circle rates (marked as sample)
- 40 property submissions spread across all statuses, types and localities with realistic Indian names, sizes in mixed units, and prices in INR
- Evaluations, site visits, offers, and 8 acquisitions, of which 6 are published as listings
- 10 buyer inquiries, 4 channel partners, 6 testimonials, 6 blog posts, FAQs
- Placeholder images generated with Pillow if no internet

## 11. Quality and delivery

- Format prices in Indian style (₹ 45,00,000 and "45 Lakh", "1.2 Crore") using a custom template filter
- CSRF on all forms, file upload validation, staff-only access for dashboard, owners can only see their own submissions
- Settings split or use environment variables for `SECRET_KEY` and `DEBUG`; `MEDIA` configured for uploads
- Write basic tests for: reference ID generation, area unit conversion, evaluation score calculation, submission form, and permissions
- Add `requirements.txt`, `.gitignore`, and a clear `README.md` with setup steps, demo logins, and a feature list
- Add `docs/DEMO_WALKTHROUGH.md`: a 5-minute script for presenting the demo to the client (owner submits property → staff evaluates → offer → owner accepts → acquired → published for resale → buyer inquiry)
- Add `docs/FUTURE_SCOPE.md` with features to explain in the proposal but not built: real SMS/WhatsApp OTP and notifications (MSG91/Twilio/WhatsApp Business API), payment escrow, Bhulekh UP land record integration, e-sign, CRM integration, mobile app, AI price prediction, PostgreSQL + cloud deployment

## 12. How to work

1. First, show me a short plan: final folder structure, models list, URL map, and build phases. Wait for my "go".
2. Build in phases and make sure the server runs after each phase:
   - Phase 1: project setup, custom user, base templates, design system, home page
   - Phase 2: locations + submissions with the multi-step sell form, tracking, estimator
   - Phase 3: owner portal and offers
   - Phase 4: staff dashboard, pipeline Kanban, evaluation, legal, acquisitions
   - Phase 5: listings, buyer inquiries, partners
   - Phase 6: SEO (meta, sitemap, robots, schema, landing pages, blog)
   - Phase 7: seed data, tests, README and docs, final polish and responsive check
3. After each phase, run `python manage.py check`, apply migrations, run tests, and fix all errors before moving on.
4. Do not leave TODOs or broken links in the demo. Every button visible in the UI must work or show a clear "Demo" message.
5. At the end, give me the exact commands to run the project and the list of demo URLs and logins.
