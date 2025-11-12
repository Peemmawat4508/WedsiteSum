# Quick Vercel Deployment Guide

## Recommended: Frontend Only on Vercel

This is the **easiest and most reliable** approach.

### Step 1: Deploy Backend Elsewhere

First, deploy your backend on Railway, Render, or another platform:
- See `DEPLOYMENT.md` for Railway/Render instructions
- Get your backend URL (e.g., `https://your-backend.railway.app`)

### Step 2: Deploy Frontend on Vercel

**Option A: Using Vercel Dashboard (Easiest)**

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **"New Project"**
3. Import your GitHub repository
4. Configure the project:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (auto-detected)
   - **Output Directory**: `dist` (auto-detected)
5. Click **"Deploy"**

**Option B: Using Vercel CLI**

```bash
cd frontend
npm i -g vercel
vercel
```

Follow the prompts:
- Set up and deploy? **Yes**
- Which scope? (Select your account)
- Link to existing project? **No**
- Project name? (Press enter for default)
- Directory? `./`
- Override settings? **No**

### Step 3: Configure Environment Variables

In Vercel dashboard, go to your project → Settings → Environment Variables:

1. **VITE_API_URL**: Your backend URL
   - Example: `https://your-backend.railway.app`
   
2. **VITE_GOOGLE_CLIENT_ID**: Your Google OAuth client ID (optional)

### Step 4: Update Backend CORS

In your backend environment variables, add your Vercel domain:

```env
CORS_ORIGINS=https://your-app.vercel.app,https://your-custom-domain.com
```

### Step 5: Redeploy

After setting environment variables, Vercel will automatically redeploy. Or manually trigger:
- Dashboard: Go to Deployments → Click "..." → Redeploy
- CLI: `vercel --prod`

## Full-Stack on Vercel (Advanced)

⚠️ **Warning**: This requires PostgreSQL (SQLite won't work) and has limitations.

### Prerequisites

1. **PostgreSQL Database**: 
   - Use Vercel Postgres, Neon, or Supabase
   - Get connection string

2. **Update requirements.txt**: Already includes `mangum`

### Deployment Steps

1. **Update database.py** to use PostgreSQL:
   ```python
   # Already configured via DATABASE_URL environment variable
   ```

2. **Deploy from project root**:
   ```bash
   vercel
   ```

3. **Configure in Vercel Dashboard**:
   - Root Directory: Leave empty
   - Build Command: `cd frontend && npm install && npm run build`
   - Output Directory: `frontend/dist`

4. **Set Environment Variables**:
   ```
   SECRET_KEY=your-secret-key
   DATABASE_URL=postgresql://user:pass@host:5432/db
   OPENAI_API_KEY=your-key
   GOOGLE_CLIENT_ID=your-client-id
   CORS_ORIGINS=https://your-app.vercel.app
   VITE_API_URL=/api
   VITE_GOOGLE_CLIENT_ID=your-client-id
   ```

5. **Deploy**:
   ```bash
   vercel --prod
   ```

## Troubleshooting

### Frontend can't connect to backend
- Check `VITE_API_URL` is set correctly
- Verify backend CORS allows your Vercel domain
- Check browser console for CORS errors

### Build fails
- Ensure all dependencies are in `package.json`
- Check build logs in Vercel dashboard
- Try building locally: `cd frontend && npm run build`

### API routes not working (full-stack)
- Verify `vercel.json` routes are correct
- Check `backend/api/index.py` exists
- Review serverless function logs in Vercel dashboard

## Custom Domain

1. Go to Project Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed
4. Update `CORS_ORIGINS` in backend to include new domain

## Need Help?

- Vercel Docs: https://vercel.com/docs
- Check deployment logs in Vercel dashboard
- Review `DEPLOYMENT.md` for other platform options

