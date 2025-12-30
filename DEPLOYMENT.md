# Deployment Guide - Vercel + Railway

This guide will help you deploy the WhatsApp Secretary AI with:
- **Frontend**: Vercel (Free tier)
- **Backend**: Railway (~$5/month)

---

## Prerequisites

1. **Vercel Account**: Sign up at https://vercel.com
2. **Railway Account**: Sign up at https://railway.app
3. **GitHub Repository**: Push your code to GitHub
4. **API Keys**: Have your OpenAI/Gemini API keys ready

---

## Part 1: Deploy Backend to Railway

### Step 1: Create New Railway Project

1. Go to https://railway.app/dashboard
2. Click "New Project"
3. Choose "Deploy from GitHub repo"
4. Select your repository
5. Railway will auto-detect the configuration

### Step 2: Configure Environment Variables

In Railway dashboard, go to your project → Variables → Add these:

```bash
# LLM API Keys
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...

# Authorization
BOSS_PHONE_NUMBER=+85290511427
BOSS_CONTACT_NAME=AIbyML.com HK
AUTHORIZATION_PASSWORD=AI((99mlMeta
UNAUTHORIZED_MESSAGE=Sorry, Mr Hung is not available at this moment, if you like leave any message or make an appointments, please let me know. We will arrange with you asap

# Database (Railway provides this automatically)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Port (Railway provides this)
PORT=8001
```

### Step 3: Add PostgreSQL Database (Optional)

1. In Railway project, click "New" → "Database" → "PostgreSQL"
2. Railway will automatically link it
3. Your `DATABASE_URL` will be available in environment variables

### Step 4: Deploy

1. Railway will automatically deploy after you push to GitHub
2. Wait for build to complete (~3-5 minutes)
3. Note your Railway URL: `https://your-app.railway.app`

### Step 5: Verify Backend

```bash
curl https://your-app.railway.app/health
```

Should return: `{"status":"healthy"}`

---

## Part 2: Deploy Frontend to Vercel

### Step 1: Install Vercel CLI (Optional)

```bash
npm install -g vercel
```

Or use Vercel Dashboard for easier setup.

### Step 2: Configure Frontend Environment

Create `.env.production` in `frontend/` folder:

```bash
VITE_API_URL=https://your-app.railway.app
VITE_WS_URL=wss://your-app.railway.app
```

**Replace `your-app.railway.app` with your actual Railway URL**

### Step 3: Deploy to Vercel

#### Option A: Using Vercel Dashboard (Recommended)

1. Go to https://vercel.com/dashboard
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Add Environment Variables:
   - `VITE_API_URL` = `https://your-app.railway.app`
   - `VITE_WS_URL` = `wss://your-app.railway.app`
6. Click "Deploy"

#### Option B: Using Vercel CLI

```bash
cd frontend
vercel login
vercel --prod
```

### Step 4: Verify Frontend

1. Open your Vercel URL: `https://your-app.vercel.app`
2. Check that it loads without errors
3. Test WhatsApp connection (scan QR code)

---

## Part 3: Connect WhatsApp

### Step 1: Access Your Deployed Frontend

Open: `https://your-app.vercel.app`

### Step 2: Scan QR Code

1. The frontend will show a QR code
2. Open WhatsApp on your phone
3. Go to Settings → Linked Devices → Link a Device
4. Scan the QR code
5. Wait for "Connected" status

### Step 3: Test the System

Send a test message to your WhatsApp number:

**From unauthorized number:**
```
What's your schedule?
```
Expected: Generic "Mr Hung not available" message

**From +852 90511427 with password:**
```
AI((99mlMeta - What appointments do we have today?
```
Expected: Full AI response with appointment details

---

## Monitoring & Logs

### Railway Logs

```bash
# In Railway dashboard
Project → Deployments → View Logs
```

Or use Railway CLI:
```bash
railway login
railway logs
```

### Vercel Logs

```bash
# In Vercel dashboard
Project → Deployments → View Function Logs
```

Or use Vercel CLI:
```bash
vercel logs
```

---

## Cost Breakdown

| Service | Plan | Cost |
|---------|------|------|
| **Vercel** | Hobby (Free) | $0/month |
| **Railway** | Starter | ~$5/month |
| **Total** | | **$5/month** |

### Railway Usage Estimate:
- 512 MB RAM: ~$0.000008/minute = ~$3.50/month
- Egress: ~$0.10/GB
- **Total**: ~$5/month for small-medium usage

---

## Troubleshooting

### Backend Not Starting

1. Check Railway logs for errors
2. Verify all environment variables are set
3. Check that `requirements.txt` includes all dependencies

### Frontend Can't Connect to Backend

1. Verify `VITE_API_URL` environment variable in Vercel
2. Check CORS settings in backend
3. Ensure Railway backend is running (check logs)

### WhatsApp Not Connecting

1. Check Railway logs for WhatsApp bridge errors
2. Verify Chromium is installed (included in `nixpacks.toml`)
3. Try redeploying the backend

### Database Connection Issues

1. Ensure PostgreSQL is added in Railway
2. Check `DATABASE_URL` environment variable
3. Verify database migrations ran

---

## Updating Deployments

### Update Backend (Railway)

```bash
git add .
git commit -m "Update backend"
git push origin main
```

Railway will auto-deploy on push.

### Update Frontend (Vercel)

```bash
git add .
git commit -m "Update frontend"
git push origin main
```

Vercel will auto-deploy on push.

---

## Security Checklist

- [ ] Change `AUTHORIZATION_PASSWORD` from default
- [ ] Update `BOSS_PHONE_NUMBER` to your actual number
- [ ] Keep API keys in environment variables (never commit)
- [ ] Enable Vercel password protection if needed
- [ ] Set up custom domain (optional)
- [ ] Enable HTTPS (automatic on Vercel/Railway)

---

## Custom Domains (Optional)

### Vercel Frontend

1. Go to Project Settings → Domains
2. Add your domain (e.g., `whatsapp.yourdomain.com`)
3. Configure DNS as instructed

### Railway Backend

1. Go to Project Settings → Domains
2. Click "Generate Domain" or add custom domain
3. Update `VITE_API_URL` in Vercel to new domain

---

## Support

- **Railway Docs**: https://docs.railway.app
- **Vercel Docs**: https://vercel.com/docs
- **GitHub Issues**: https://github.com/yourusername/whatsapp-secretary-ai/issues

---

**Deployment Complete!** Your WhatsApp Secretary AI is now live on Vercel + Railway. 🚀
