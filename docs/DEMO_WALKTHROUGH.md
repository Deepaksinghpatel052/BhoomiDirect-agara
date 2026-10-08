# 5-Minute Demo Script

Before the meeting run `python manage.py seed_demo` (fresh data) and `python manage.py runserver`. Keep two browser windows: a normal one (owner/public) and a private one (staff).

## 0:00 Positioning (30 sec)
Open `/`. "This isn't a listing portal. Owners sell directly to you. Every button pushes them to *Sell Your Property*."
- Point out: hero headline, quick form, trust counters, 5 steps, areas map, testimonials.
- Click **हिं** to show the Hindi toggle on the hero and CTAs.

## 0:30 Owner submits a property (1 min 15 sec)
Click **Submit Your Property**.
1. Step 1: name + mobile → the **OTP** appears on screen (marked DEMO) → verify.
2. Step 2: pick *Agricultural Land*, tehsil *Etmadpur*, locality *Agra-Lucknow Expressway Belt*. The map jumps there; tap to drop a pin.
3. Step 3: type `5` and choose *Bigha*. The **live converter** shows sq ft, gaj and acres. The agricultural fields are visible because the type is agricultural.
4. Step 4: tick *Any loan*. The details box appears (conditional logic).
5. Step 5: price `6000000` shows "₹ 60 Lakh". Drag in photos, tick consent, submit.
- Thank-you page: reference ID, **WhatsApp share**, **Track** button. Click Track to show the timeline.

## 1:45 Price estimator and SEO pages (30 sec)
- `/price-estimator/`: Fatehabad Road, residential plot, 200 gaj → instant range plus the disclaimer.
- `/sell-land-in-agra/fatehabad-road/`: a unique SEO page with sample circle rates, FAQ and lead form. Mention `sitemap.xml`, schema and `docs/SEO_STRATEGY.md`.

## 2:15 Staff evaluates (1 min)
In the private window log in as `admin / admin123` → `/dashboard/`.
- KPIs and charts (leads per week, localities, types, funnel).
- **Pipeline board**: the new lead is in *New*. Drag it to *Contacted*; a toast confirms and status history is saved.
- Open the lead: photos, map, call/WhatsApp buttons.
  - **Site visits** tab: schedule a visit for agent Ravi.
  - **Evaluation** tab: move the sliders. The score, recommendation (Strong Buy / Consider / Reject) and margin update live. Save.
  - **Legal** tab: tick items and watch the progress bar.
  - **Offers** tab: create an offer of ₹ 55 Lakh.

## 3:15 Owner responds (45 sec)
Back in the owner window, log in as `owner / demo123` (or sign up with the mobile used in the form).
- `/my/` shows an open-offer alert. Open the property, see the timeline, then **Counter** or **Accept** (the demo owner's `BDA-…00001` already has an open offer).
- The bell icon shows notifications.

## 4:00 Acquire and publish for resale (40 sec)
Staff window, same lead (status *Offer Accepted*):
- **Mark as acquired**: stamp duty and registration are pre-filled, and the total cost is calculated.
- Click **Publish for Resale**. The listing is created with photos, then the edit screen opens.

## 4:40 Buyer inquiry and partners (20 sec)
- Open the public listing `/buy-property-in-agra/…` and send an inquiry. It shows a toast and appears in **Buyer inquiries**.
- Show **Inventory & sales** (profit on a sold listing) and **Channel partners** (approve a partner). Log in as `partner / demo123` to show the partner portal.

## Close
"Everything you saw runs today. Real SMS/WhatsApp, payments and land-record integration are next (see `docs/FUTURE_SCOPE.md`)."
