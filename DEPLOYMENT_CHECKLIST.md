# 🚀 Deployment Checklist - What to Switch/Change

When deploying from local development to production, here are **ALL the things** you need to change:

---

## 📋 **Backend Changes (Required)**

### 1. **Environment Variables** ⚠️ CRITICAL

Create a `.env` file or set these in your hosting platform:

```bash
# Required
SECRET_KEY=your-very-secure-random-secret-key-here  # Change from default!
DATABASE_URL=postgresql://user:pass@host:5432/dbname  # Switch from SQLite to PostgreSQL
CORS_ORIGINS=https://your-frontend-domain.com  # Change from localhost

# Optional but recommended
OPENAI_API_KEY=your-openai-key  # If you have one
GOOGLE_CLIENT_ID=your-google-client-id  # If using Google OAuth
```

**Files to update:**
- `backend/.env` (create if doesn't exist)
- Or set in hosting platform (Railway/Render/Vercel)

---

### 2. **Database** 🔄 MUST SWITCH

**Current (Local):** SQLite (`sqlite:///./documents.db`)  
**Production:** PostgreSQL

**What to do:**
1. Set up PostgreSQL database:
   - Railway: Auto-provided
   - Render: Create PostgreSQL service
   - Vercel: Use Vercel Postgres or Neon/Supabase
2. Update `DATABASE_URL` environment variable
3. Database will auto-migrate on first run

**File:** `backend/database.py` (already configured to use `DATABASE_URL` env var)

---

### 3. **CORS Origins** 🌐 MUST UPDATE

**Current:** `http://localhost:3000,http://localhost:5173`  
**Production:** Your actual frontend domain

**What to change:**
```bash
# In backend environment variables
CORS_ORIGINS=https://your-app.vercel.app,https://www.yourdomain.com
```

**File:** `backend/main.py` (line 33) - reads from `CORS_ORIGINS` env var

---

### 4. **Secret Key** 🔐 MUST CHANGE

**Current:** `"your-secret-key-change-in-production"` (default)  
**Production:** Strong random secret key

**Generate a secure key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**File:** `backend/main.py` (line 43) - reads from `SECRET_KEY` env var

---

## 📋 **Frontend Changes (Required)**

### 5. **API URL** 🔗 MUST UPDATE

**Current:** `http://localhost:8000`  
**Production:** Your backend URL

**What to change:**
Set environment variable in Vercel/hosting platform:
```bash
VITE_API_URL=https://your-backend.railway.app
# OR
VITE_API_URL=https://your-backend.render.com
```

**Files that use it:**
- `frontend/src/utils/auth.js` (line 1) ✅ Already uses env var
- `frontend/src/components/Dashboard.jsx` (line 157) ✅ Already uses env var
- `frontend/src/components/Login.jsx` (line 29) ⚠️ **NEEDS FIX**
- `frontend/src/components/Register.jsx` (line 40) ⚠️ **NEEDS FIX**

---

### 6. **Google OAuth Client ID** (Optional)

**Current:** Empty or localhost  
**Production:** Production OAuth client ID

**What to change:**
1. Create OAuth credentials in Google Cloud Console
2. Add authorized redirect URIs:
   - `https://your-frontend.vercel.app`
3. Set environment variable:
```bash
VITE_GOOGLE_CLIENT_ID=your-production-client-id
```

---

## 📋 **Code Fixes Needed**

### 7. **Hardcoded API URLs** ⚠️ MUST FIX

**Files with hardcoded `localhost:8000`:**

1. **`frontend/src/components/Login.jsx`** (line 29)
   ```javascript
   // CURRENT (WRONG):
   const response = await fetch('http://localhost:8000/token', {
   
   // SHOULD BE:
   const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/token`, {
   ```

2. **`frontend/src/components/Register.jsx`** (line 40)
   ```javascript
   // CURRENT (WRONG):
   const loginResponse = await fetch('http://localhost:8000/token', {
   
   // SHOULD BE:
   const loginResponse = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/token`, {
   ```

---

## 📋 **Infrastructure Changes**

### 8. **File Storage** (If needed)

**Current:** Local file system  
**Production:** Cloud storage (if storing files)

**Options:**
- AWS S3
- Cloudinary
- Vercel Blob Storage
- Or keep in database (current approach)

**Note:** Currently files are stored in database, so no change needed unless you want to optimize.

---

### 9. **Tesseract OCR** (For image support)

**Current:** Local installation  
**Production:** Install on server or use cloud OCR

**Options:**
- Install Tesseract on server (Railway/Render)
- Use cloud OCR service (Google Vision API, AWS Textract)
- Or disable image OCR in production

---

## 📋 **Build & Deploy Settings**

### 10. **Build Commands**

**Frontend (Vercel):**
- Build Command: `npm run build` ✅ (auto-detected)
- Output Directory: `dist` ✅ (auto-detected)
- Install Command: `npm install` ✅ (auto-detected)

**Backend (Railway/Render):**
- Build Command: `pip install -r requirements.txt` ✅
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT` ✅

---

## 📋 **Security Checklist**

### 11. **Security Settings**

- [ ] Change `SECRET_KEY` to strong random value
- [ ] Use HTTPS (automatic on Vercel/Railway/Render)
- [ ] Set proper `CORS_ORIGINS` (no wildcards in production)
- [ ] Don't commit `.env` files to Git
- [ ] Use environment variables for all secrets
- [ ] Enable rate limiting (optional but recommended)

---

## 📋 **Quick Summary - 7 Things to Switch**

1. ✅ **SECRET_KEY** - Generate new secure key
2. ✅ **DATABASE_URL** - Switch from SQLite to PostgreSQL
3. ✅ **CORS_ORIGINS** - Change from localhost to production domain
4. ✅ **VITE_API_URL** - Change from localhost to backend URL
5. ⚠️ **Fix hardcoded URLs** - Update Login.jsx and Register.jsx
6. ✅ **VITE_GOOGLE_CLIENT_ID** - Update if using Google OAuth
7. ✅ **Tesseract OCR** - Install on server or disable image OCR

---

## 🎯 **Recommended Deployment Order**

1. **Deploy Backend First** (Railway/Render)
   - Set all backend environment variables
   - Get backend URL

2. **Fix Frontend Code**
   - Update Login.jsx and Register.jsx to use env vars

3. **Deploy Frontend** (Vercel)
   - Set `VITE_API_URL` to backend URL
   - Set `VITE_GOOGLE_CLIENT_ID` if needed

4. **Update Backend CORS**
   - Add frontend URL to `CORS_ORIGINS`

5. **Test Everything**
   - Register/Login
   - Upload document
   - Generate summary
   - Test all features

---

## 📝 **Environment Variables Template**

### Backend (.env or hosting platform)
```bash
SECRET_KEY=generate-strong-random-key-here
DATABASE_URL=postgresql://user:pass@host:5432/dbname
CORS_ORIGINS=https://your-frontend.vercel.app
OPENAI_API_KEY=sk-... (optional)
GOOGLE_CLIENT_ID=... (optional)
```

### Frontend (Vercel environment variables)
```bash
VITE_API_URL=https://your-backend.railway.app
VITE_GOOGLE_CLIENT_ID=... (optional)
```

---

## ✅ **After Deployment**

- [ ] Test registration
- [ ] Test login
- [ ] Test document upload
- [ ] Test summary generation
- [ ] Test grammar checker
- [ ] Test chat
- [ ] Test image generator
- [ ] Check browser console for errors
- [ ] Verify HTTPS is working
- [ ] Test on mobile device

---

**Need help?** Check `DEPLOYMENT.md` for detailed step-by-step instructions.

