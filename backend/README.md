# college  culture Luxury Accessories — Backend API

Backend service for **college  culture (Beyond Ordinary)**, an ultra-premium men's jewellery & accessories e-commerce platform.

---

## 🔑 API KEYS — WHERE TO ADD THEM

This application features a centralized, zero-leakage backend integration management system powered by **Pydantic Settings** (`backend/app/core/config.py`).

### 📁 One Central Place for All Credentials: `backend/.env`
All API credentials and database connection strings are configured in a single, organized file:
```text
backend/.env
```
*(In production, these same variable names are entered into your hosting provider's Secrets / Environment Variables panel).*

---

### 🛡️ Critical Security Rules

1. **Backend Only**: Never expose secret API keys to frontend users or web clients.
2. **Never in Databases**: Never store secret API keys inside PostgreSQL or Supabase tables.
3. **Never Hardcoded**: Never hardcode API keys inside Python, JavaScript, TypeScript, React, or Next.js source code.
4. **Never Committed to Git**: `backend/.env` is git-ignored by `.gitignore`. Real API keys must never be pushed to GitHub.
5. **Never in API Responses**: The backend never returns secrets, tokens, passwords, or connection strings in HTTP responses.
6. **Graceful Startup**: Optional integrations never prevent the FastAPI backend from starting. Only required services are validated.

---

### 🏛️ Architecture: Frontend (Vercel) to Backend (FastAPI)

```text
       Vercel Frontend (Next.js / React)
                      │
                      │  NEXT_PUBLIC_API_URL (e.g. https://api.yourdomain.com)
                      ▼
               FastAPI Backend
                      │
       ┌──────────────┼──────────────┬──────────────┬──────────────┐
       ▼              ▼              ▼              ▼              ▼
   Gemini AI      Database       Razorpay         Unstop        Resend &
  (Stylist Chat) (PostgreSQL)  (Order/Verify)    (Scraper)      Firebase
```

- **Frontend on Vercel**: Needs **ONLY** `NEXT_PUBLIC_API_URL=https://your-backend-api.com`.
- **Backend on Server / Cloud**: Holds `backend/.env` with private credentials.

---

### 📊 Integrations Table & Status Classification

| Service | Environment Variable(s) | Required? | Purpose in Application |
| :--- | :--- | :--- | :--- |
| **Gemini AI** | `GEMINI_API_KEY` | **Required** (if AI features used) | Powers AI Stylist, outfit pairing advice, and conversational recommendation. |
| **Database** | `DATABASE_URL`<br>`SUPABASE_URL`<br>`SUPABASE_ANON_KEY`<br>`SUPABASE_SERVICE_ROLE_KEY` | **Required** (for persistence) | Application database for product catalog, orders, cart persistence, and user accounts. |
| **Razorpay** | `RAZORPAY_KEY_ID`<br>`RAZORPAY_KEY_SECRET` | **Required** (for checkout) | Server-side Razorpay order generation and HMAC-SHA256 signature verification. |
| **Google Maps** | `GOOGLE_MAPS_API_KEY` | **Optional** | Map rendering, address geolocation, and delivery proximity inference. |
| **Google Places** | `GOOGLE_PLACES_API_KEY` | **Optional / Not Currently Used** | Autocomplete and place search for shipping addresses. |
| **Unstop Scraper** | `UNSTOP_SCRAPER_API_URL`<br>`UNSTOP_SCRAPER_API_KEY` | **Optional** (ready to integrate) | Apify actor proxy for hackathons, competitions, and opportunities. |
| **Resend (Email)** | `RESEND_API_KEY` | **Optional** | Transactional emails (order confirmation receipts, notifications). |
| **Firebase** | `FIREBASE_PROJECT_ID`<br>`FIREBASE_CLIENT_EMAIL`<br>`FIREBASE_PRIVATE_KEY` | **Optional** | Push notifications and Firebase Cloud Messaging (FCM). |

---

### 🌐 Where to Obtain Each Credential

1. **Gemini AI**:
   - URL: [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Click "Create API Key" and copy the key into `GEMINI_API_KEY`.
2. **Supabase / PostgreSQL**:
   - URL: [Supabase Dashboard](https://supabase.com/dashboard)
   - Go to **Project Settings** -> **API** to copy `Project URL`, `anon public` key, and `service_role` key.
   - Go to **Project Settings** -> **Database** -> **Connection string** (URI) for `DATABASE_URL`.
3. **Razorpay**:
   - URL: [Razorpay Dashboard](https://dashboard.razorpay.com/#/app/keys)
   - Go to **Settings** -> **API Keys** -> Generate Test/Live Key.
   - Copy `Key Id` (`RAZORPAY_KEY_ID`) and `Key Secret` (`RAZORPAY_KEY_SECRET`).
4. **Google Maps & Places**:
   - URL: [Google Cloud Console](https://console.cloud.google.com/google/maps-apis)
   - Enable "Maps JavaScript API" / "Places API" and generate an API key.
5. **Unstop Scraper (Apify)**:
   - URL: [Apify Console](https://console.apify.com/account/integrations)
   - Copy your Apify personal API token (`apify_api_...`) and configure the actor URL in `UNSTOP_SCRAPER_API_URL`.
6. **Resend (Email)**:
   - URL: [Resend API Keys](https://resend.com/api-keys)
   - Create an API key (`re_...`) and add verified domain sender.
7. **Firebase**:
   - URL: [Firebase Console](https://console.firebase.google.com/)
   - Go to **Project Settings** -> **Service accounts** -> **Generate new private key** (JSON file).
   - Copy `project_id`, `client_email`, and `private_key` into the `.env` variables.

---

### 💻 Local Development Setup

1. Copy `.env.example` to `backend/.env`:
   ```bash
   cp backend/.env.example backend/.env
   ```
2. Open `backend/.env` in your editor and paste your credentials into the appropriate sections:
   ```env
   # 🤖 GEMINI AI
   GEMINI_API_KEY=your_gemini_key

   # 🗄️ DATABASE / SUPABASE
   DATABASE_URL=postgresql://postgres:...@db...supabase.co:5432/postgres
   SUPABASE_URL=https://...supabase.co/rest/v1/
   SUPABASE_ANON_KEY=eyJ...
   SUPABASE_SERVICE_ROLE_KEY=eyJ...

   # 🗺️ GOOGLE MAPS
   GOOGLE_MAPS_API_KEY=AIzaSy...
   GOOGLE_PLACES_API_KEY=

   # 🏆 UNSTOP SCRAPER API
   UNSTOP_SCRAPER_API_URL=https://api.apify.com/v2/acts/solidcode~unstop-scraper/run-sync-get-dataset-items
   UNSTOP_SCRAPER_API_KEY=apify_api_...

   # 💳 RAZORPAY
   RAZORPAY_KEY_ID=rzp_test_...
   RAZORPAY_KEY_SECRET=...

   # 📧 EMAIL (RESEND)
   RESEND_API_KEY=re_...

   # 🔔 FIREBASE
   FIREBASE_PROJECT_ID=...
   FIREBASE_CLIENT_EMAIL=...
   FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"

   # 🌐 APPLICATION
   FRONTEND_URL=http://localhost:3000
   ENVIRONMENT=development
   PORT=8000
   ```
3. Start the backend:
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```

---

### 🚀 Production Deployment (Vercel + Backend Host)

#### 1. Backend Host (Render, Railway, Fly.io, AWS, DigitalOcean)
- **Do NOT upload `.env` to GitHub.**
- Open your backend hosting service dashboard.
- Navigate to **Environment Variables** / **Secrets**.
- Paste all the variable names and their production values.
- Set:
  ```env
  ENVIRONMENT=production
  FRONTEND_URL=https://your-app-domain.vercel.app
  ```

#### 2. Frontend Host (Vercel)
- In the Vercel Project Settings -> **Environment Variables**:
  ```env
  NEXT_PUBLIC_API_URL=https://your-deployed-fastapi-backend.com
  ```
- No database credentials, Razorpay secret keys, or service role keys should ever be placed in Vercel!

---

### 🧪 Verification: How to Check Configuration Status

#### 1. At Startup (Console Log)
When the backend starts, it automatically analyzes which integrations are configured and outputs clean checkmarks with **ZERO secret leakage**:
```text
==================================================
⚙️  API INTEGRATIONS CONFIGURATION STATUS
==================================================
✓ Database: Configured
✓ Gemini AI: Configured
✓ Google Maps: Configured
✗ Google Places: Not configured
✓ Unstop Scraper: Configured
✓ Razorpay: Configured
✓ Email: Configured
✓ Firebase: Configured
==================================================
Environment: development
==================================================
```

#### 2. Protected Admin API Endpoint (`GET /api/config/status`)
Authorized administrators can inspect integration status at runtime:
```http
GET /api/config/status
Authorization: Bearer <ADMIN_JWT_TOKEN>
```
Response (Strictly Booleans):
```json
{
  "gemini": true,
  "database": true,
  "google_maps": true,
  "google_places": false,
  "unstop_scraper": true,
  "razorpay": true,
  "email": true,
  "firebase": true
}
```
*Notice: Secrets, passwords, keys, and connection strings are strictly omitted.*

---

## 📁 Backend Directory Structure

```text
backend/
├── app/
│   ├── core/
│   │   └── config.py        # Centralized Pydantic Settings & status detection
│   ├── main.py              # FastAPI application, startup banners & CORS
│   ├── config.py            # Backward-compatible re-exporter
│   ├── routes/              # Modular API routers
│   │   ├── auth.py          # /api/auth (register, login, me)
│   │   ├── config.py        # /api/config/status (admin-only status check)
│   │   ├── products.py      # /api/products (catalog, filters, details)
│   │   ├── cart.py          # /api/cart (add, update, delete, summary)
│   │   ├── wishlist.py      # /api/wishlist (get, toggle)
│   │   ├── orders.py        # /api/orders (creation, tracking)
│   │   ├── payment.py       # /api/payment (create-order, verify)
│   │   ├── ai.py            # /api/ai (recommendation, descriptions, chat)
│   │   └── unstop.py        # /api/unstop (scraper dataset items proxy)
│   ├── services/
│   │   ├── gemini.py        # Gemini Flash AI service
│   │   ├── payment.py       # Razorpay order generation & signature verify
│   │   ├── products.py      # Price validation & catalog filtering
│   │   └── unstop.py        # Apify actor proxy client for Unstop scraper
│   ├── database/
│   │   ├── supabase.py      # Supabase PostgREST async client & fallback
│   │   ├── schema.sql       # Database table definitions & RLS
│   │   └── seed_data.py     # Authentic college  culture accessories catalog
│   └── security/
│       ├── auth.py          # Bcrypt hashing, JWT & admin role verification
│       └── rate_limiter.py  # SlowAPI rate limiting configuration
├── tests/
│   └── test_backend.py      # Automated integration test suite
├── .env                     # Private secrets (GIT-IGNORED)
├── .env.example             # Safe template with placeholders
├── .gitignore               # Strict ignore rules
├── requirements.txt         # Python dependencies
└── README.md
```

---

## 🧪 Running Automated Tests

Run the backend test suite:
```bash
python tests/test_backend.py
```
This tests:
1. Environment variables loading and detection logic
2. Startup banner output safety (zero secret leak)
3. Health endpoint (`/health`)
4. Product catalog & detail endpoints
5. Auth registration, login, and JWT verification
6. Admin-protected `/api/config/status` endpoint
7. Cart & wishlist operations
8. Gemini AI style recommendations
9. Razorpay order generation & HMAC-SHA256 signature verification
10. Unstop scraper proxy routing

---

## 🗄️ Setting up Supabase Database

1. Open your Supabase Dashboard.
2. Navigate to **SQL Editor** -> **New query**.
3. Open `backend/app/database/schema.sql` and paste its contents.
4. Click **Run** to provision the tables, foreign keys, indexes, and Row Level Security (RLS) policies.
