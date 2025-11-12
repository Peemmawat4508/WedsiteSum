# Vercel Deployment Guide

Simple step-by-step guide to deploy your Document Summarizer on Vercel.

## 🎯 Recommended: Frontend on Vercel

This is the easiest and most reliable approach. Deploy your frontend on Vercel and backend on Railway or Render.

---

## Step 1: Deploy Backend First

You need to deploy your backend on Railway or Render first, then connect it to Vercel.

### Option A: Railway (Recommended)

1. Go to https://railway.app
2. Sign in with GitHub
3. Click **"New Project"** → **"Deploy from GitHub repo"**
4. Select your repository
5. Click **"Add Service"** → **"GitHub Repo"**
6. Select your repo again
7. In the service settings:
   - **Root Directory:** `backend`
   - Railway will auto-detect Python
8. Go to **Variables** tab and add:
   ```
   SECRET_KEY=your-secure-secret-key-here
   DATABASE_URL=postgresql://... (Railway provides this automatically)
   OPENAI_API_KEY=your-key (optional)
   GOOGLE_CLIENT_ID=your-client-id (optional)
   CORS_ORIGINS=http://localhost:3000
   ```
9. Copy your Railway URL (e.g., `https://your-app.railway.app`)

### Option B: Render

1. Go to https://render.com
2. Sign in with GitHub
3. Click **"New"** → **"Web Service"**
4. Connect your GitHub repository
5. Configure:
   - **Name:** `document-summarizer-backend`
   - **Root Directory:** `backend`
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables (same as Railway above)
7. Click **"Create Web Service"**
8. Copy your Render URL

---

## Step 2: Deploy Frontend on Vercel

### Using Vercel Dashboard (Easiest)

1. **Go to Vercel:**
   - Visit https://vercel.com
   - Sign in with GitHub

2. **Create New Project:**
   - Click **"Add New..."** → **"Project"**
   - Import your GitHub repository
   - Click **"Import"**

3. **Configure Project:**
   - **Framework Preset:** Vite (auto-detected)
   - **Root Directory:** Click **"Edit"** → Change to `frontend`
   - **Build Command:** `npm run build` (auto-filled)
   - **Output Directory:** `dist` (auto-filled)
   - **Install Command:** `npm install` (auto-filled)

4. **Add Environment Variables:**
   Click **"Environment Variables"** and add:
   
   - **Name:** `VITE_API_URL`
   - **Value:** Your backend URL (e.g., `https://your-app.railway.app`)
   - **Environment:** Select all (Production, Preview, Development)
   - Click **"Save"**
   
   - **Name:** `VITE_GOOGLE_CLIENT_ID` (optional)
   - **Value:** Your Google OAuth client ID
   - **Environment:** Select all
   - Click **"Save"**

5. **Deploy:**
   - Click **"Deploy"**
   - Wait 2-3 minutes for build to complete
   - You'll get a URL like `https://your-app.vercel.app`

### Using Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to frontend directory
cd frontend

# Login
vercel login

# Deploy
vercel

# Set environment variables
vercel env add VITE_API_URL
# Enter your backend URL when prompted

vercel env add VITE_GOOGLE_CLIENT_ID
# Enter your Google client ID when prompted

# Deploy to production
vercel --prod
```

---

## Step 3: Update Backend CORS

Go back to your backend (Railway or Render) and update the `CORS_ORIGINS` environment variable:

1. **Railway:** Settings → Variables → Edit `CORS_ORIGINS`
2. **Render:** Environment → Edit `CORS_ORIGINS`

Add your Vercel URL:
```
CORS_ORIGINS=http://localhost:3000,https://your-app.vercel.app
```

Replace `your-app.vercel.app` with your actual Vercel domain.

---

## Step 4: Test Your Deployment

1. Visit your Vercel URL: `https://your-app.vercel.app`
2. Try registering/logging in
3. Upload a document
4. Generate a summary

If you see CORS errors:
- ✅ Check `VITE_API_URL` is correct in Vercel
- ✅ Verify `CORS_ORIGINS` includes your Vercel domain in backend

---

## 🚀 Full-Stack on Vercel (Advanced)

⚠️ **Note:** This requires PostgreSQL (SQLite won't work on Vercel serverless functions)

### Prerequisites

1. **Set up PostgreSQL:**
   - Option A: Vercel Postgres (in Vercel dashboard)
   - Option B: Neon (https://neon.tech) - Free tier
   - Option C: Supabase (https://supabase.com) - Free tier

2. **Get PostgreSQL connection string:**
   ```
   postgresql://user:password@host:5432/dbname
   ```

### Deployment Steps

1. **Deploy from Project Root:**
   ```bash
   npm install -g vercel
   vercel login
   vercel
   ```

2. **Configure in Vercel Dashboard:**
   - Go to your project settings
   - **Root Directory:** Leave empty (project root)
   - **Build Command:** `cd frontend && npm install && npm run build`
   - **Output Directory:** `frontend/dist`

3. **Set Environment Variables:**
   ```
   SECRET_KEY=your-very-secure-secret-key
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   OPENAI_API_KEY=your-openai-key
   GOOGLE_CLIENT_ID=your-google-client-id
   CORS_ORIGINS=https://your-app.vercel.app
   VITE_API_URL=/api
   VITE_GOOGLE_CLIENT_ID=your-google-client-id
   ```

4. **Deploy:**
   ```bash
   vercel --prod
   ```

---

## 🔧 Troubleshooting

### Frontend can't connect to backend
- ✅ Check `VITE_API_URL` is correct in Vercel
- ✅ Verify backend is running and accessible
- ✅ Check browser console (F12) for errors
- ✅ Verify CORS settings in backend

### Build fails
- ✅ Check Vercel build logs in dashboard
- ✅ Ensure all dependencies in `package.json`
- ✅ Try building locally: `cd frontend && npm run build`

### CORS errors
- ✅ Add Vercel domain to backend `CORS_ORIGINS`
- ✅ Format: `https://your-app.vercel.app` (with https, no trailing slash)

### Database errors (full-stack)
- ✅ Verify `DATABASE_URL` is PostgreSQL (not SQLite)
- ✅ Check database connection string format
- ✅ Ensure database is accessible from Vercel

---

## 📝 Quick Checklist

**Frontend Only (Recommended):**
- [ ] Backend deployed on Railway/Render
- [ ] Backend URL copied
- [ ] Frontend deployed on Vercel
- [ ] `VITE_API_URL` set in Vercel
- [ ] `CORS_ORIGINS` updated in backend
- [ ] Tested deployment

**Full-Stack:**
- [ ] PostgreSQL database set up
- [ ] `DATABASE_URL` configured
- [ ] All environment variables set
- [ ] Deployed from project root
- [ ] Tested deployment

---

## 🎉 You're Done!

Your app should now be live at `https://your-app.vercel.app`

**Need help?**
- Vercel logs: Dashboard → Deployments → Click deployment → View logs
- Backend logs: Railway/Render dashboard
- Browser console: F12 → Console tab

---

## Environment Variables Reference

### Backend (Railway/Render)
- `SECRET_KEY` - JWT secret key (required)
- `DATABASE_URL` - Database connection (PostgreSQL recommended)
- `OPENAI_API_KEY` - OpenAI API key (optional)
- `GOOGLE_CLIENT_ID` - Google OAuth client ID (optional)
- `CORS_ORIGINS` - Allowed origins (comma-separated)

### Frontend (Vercel)
- `VITE_API_URL` - Backend API URL (required)
- `VITE_GOOGLE_CLIENT_ID` - Google OAuth client ID (optional)

**Note:** Frontend variables must be prefixed with `VITE_` to be accessible in React.
