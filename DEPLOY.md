# Deploying Navil Cloud to navil.ai

This guide deploys the Navil Cloud dashboard to **Railway** and points `navil.ai` at it.
Total time: ~20 minutes.

---

## Prerequisites

- GitHub repo with this code (push main to trigger auto-deploy)
- Railway account at [railway.app](https://railway.app) (free to start)
- Clerk account at [clerk.com](https://clerk.com) (free tier is fine)
- DNS access for `navil.ai`

---

## Step 1 — Create a Clerk application

1. Go to [dashboard.clerk.com](https://dashboard.clerk.com) → **Create application**
2. Name it `navil` → choose sign-in methods (Email + Google recommended) → **Create**
3. In the Clerk dashboard, go to **API Keys**:
   - Copy **Publishable key** → `VITE_CLERK_PUBLISHABLE_KEY` (starts with `pk_live_`)
   - Copy **Secret key** → `CLERK_SECRET_KEY` (starts with `sk_live_`)
4. Go to **Configure → Domains** → **Add domain** → enter `navil.ai`
5. Go to **Configure → JWT Templates** → click the **Default** template:
   - Copy the **Issuer** URL → `CLERK_ISSUER_URL` (e.g. `https://xxx.clerk.accounts.dev`)

---

## Step 2 — Deploy to Railway

### 2a. Create the Railway project

1. Go to [railway.app/new](https://railway.app/new) → **Deploy from GitHub repo**
2. Select your `navil` repository → **Deploy now**
3. Railway detects `railway.toml` and `Dockerfile` automatically.

### 2b. Set runtime environment variables

In the Railway dashboard → your service → **Variables** tab, add:

| Variable | Value |
|---|---|
| `CLERK_SECRET_KEY` | `sk_live_...` |
| `CLERK_ISSUER_URL` | `https://xxx.clerk.accounts.dev` |
| `ALLOWED_ORIGINS` | `https://navil.ai,https://www.navil.ai` |
| `ANTHROPIC_API_KEY` *(optional)* | `sk-ant-...` |

### 2c. Set the Clerk publishable key as a **Build Variable**

The frontend key is baked into the JavaScript bundle at build time — it must be a **build variable**, not a runtime variable.

1. Railway dashboard → your service → **Settings** → **Build** section
2. Under **Build Arguments**, add:
   - `VITE_CLERK_PUBLISHABLE_KEY` = `pk_live_...`
3. Trigger a redeploy (Railway → **Redeploy** button).

### 2d. Verify the deployment

Once the build succeeds, Railway gives you a temporary URL like `navil-production-xxxx.up.railway.app`.
Open it — you should see the Navil Cloud sign-in page.

---

## Step 3 — Connect navil.ai

### 3a. Add the domain in Railway

1. Railway → your service → **Settings** → **Networking** → **Add Custom Domain**
2. Enter `navil.ai` → Railway shows you a CNAME or A record to add.

### 3b. Update DNS

Add the record Railway provides to your DNS registrar:

```
Type:  CNAME
Name:  navil.ai  (or @)
Value: <the value Railway shows>
TTL:   300
```

For `www.navil.ai` (redirect to root), add a second CNAME:

```
Type:  CNAME
Name:  www
Value: navil.ai
TTL:   300
```

Railway provisions a TLS certificate automatically once DNS propagates (~5 minutes).

---

## Step 4 — Update Clerk's allowed origins

1. Clerk dashboard → **Configure → Domains** → confirm `navil.ai` is listed
2. Clerk dashboard → **Configure → Paths**:
   - Sign-in URL: `https://navil.ai/sign-in`
   - Sign-up URL: `https://navil.ai/sign-up`
   - After sign-in: `https://navil.ai/`
   - After sign-up: `https://navil.ai/`

---

## Auto-deploys

Every push to `main` triggers a Railway rebuild. The Dockerfile builds the dashboard
(with the Clerk key baked in) and installs the Python backend in a single image.

---

## Local development

```bash
# Terminal 1: backend
pip install -e ".[cloud,llm]"
python -m navil cloud serve --port 8484

# Terminal 2: frontend (proxies /api → localhost:8484)
cd dashboard
cp .env.example .env.local          # add VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
npm install
npm run dev
```

Use the Clerk **development** keys (`pk_test_` / `sk_test_`) locally — they allow
`localhost` without domain verification.

---

## Environment variables reference

| Variable | Where to set | Required | Description |
|---|---|---|---|
| `CLERK_SECRET_KEY` | Railway runtime | Yes (for auth) | Clerk backend secret key |
| `CLERK_ISSUER_URL` | Railway runtime | Yes (for auth) | Clerk JWT issuer URL |
| `VITE_CLERK_PUBLISHABLE_KEY` | Railway **build var** | Yes (for auth) | Clerk frontend publishable key |
| `ALLOWED_ORIGINS` | Railway runtime | Recommended | Comma-separated allowed CORS origins |
| `ANTHROPIC_API_KEY` | Railway runtime | No | Enables Anthropic LLM features |
| `OPENAI_API_KEY` | Railway runtime | No | Enables OpenAI LLM features |
| `GEMINI_API_KEY` | Railway runtime | No | Enables Gemini LLM features |
| `PORT` | Set by Railway | Auto | Railway injects this automatically |
