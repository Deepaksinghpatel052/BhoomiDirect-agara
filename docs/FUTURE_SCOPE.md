# Future Scope (for the proposal, not built in the demo)

| Area | What it adds | Notes |
|---|---|---|
| Real OTP & notifications | SMS OTP, status SMS, WhatsApp updates to owners and agents | MSG91 / Twilio for SMS, WhatsApp Business API (Gupshup / Interakt / Meta Cloud API) |
| Payment escrow | Token amount and milestone payments held in escrow | Razorpay / Cashfree escrow, bank tie-up for RTGS at registry |
| UP land records | Auto-fetch Khatauni and khasra details by village and gata number | UP Bhulekh integration / scraping service, IGRS UP for registry and circle-rate data |
| e-Sign & documents | Sign offer letters and agreements online | Aadhaar e-Sign (Leegality, Digio), DigiLocker document pull |
| CRM integration | Sync leads, calls and deals | Zoho CRM / LeadSquared / HubSpot, click-to-call with call recording (Exotel / Knowlarity) |
| Mobile apps | Field agent app (offline visit reports, GPS photos) and owner app | Flutter or React Native with this Django backend as a REST API |
| AI price prediction | Model trained on acquisitions, listings and circle rates for instant valuations | Gradient boosting on deal data plus satellite or road-access features |
| Full Hindi site | Complete Hindi translation with Hindi SEO pages | Django i18n, `hi` URL prefix |
| Analytics | Funnel, source ROI, agent performance | GA4, Search Console, Metabase dashboards |
| Infrastructure | Production hosting | PostgreSQL, S3-compatible private storage for documents, Gunicorn + Nginx, AWS / DigitalOcean / Azure, daily backups, HTTPS |
| Security & compliance | Audit trail, 2FA for staff, DPDP Act 2023 consent management | django-otp, data retention policies |
| Marketing automation | Drip messages to "just exploring" owners, re-engagement | WhatsApp templates, email campaigns |
