# Quick Vercel Deployment Guide

## ✅ Step 1: Code Pushed to GitHub
Your code has been successfully pushed to: `https://github.com/Bharath2805/eu_bot`

## 🚀 Step 2: Deploy via Vercel Dashboard (Recommended)

### Deploy Backend:

1. Go to https://vercel.com and sign in (or create account)
2. Click **"Add New Project"**
3. Click **"Import Git Repository"**
4. Select **"Bharath2805/eu_bot"**
5. Configure:
   - **Framework Preset**: Other
   - **Root Directory**: `backend` (click "Edit" and type `backend`)
   - **Build Command**: Leave empty
   - **Output Directory**: Leave empty
6. Click **"Environment Variables"** and add:
   ```
   OPENAI_API_KEY = [your OpenAI API key]
   TAVILY_API_KEY = [your Tavily API key]
   VECTOR_STORE_ID = vs_692180726b908191af2f182b14342882
   CORS_ORIGINS = [leave empty for now, update after frontend deploy]
   ```
7. Click **"Deploy"**
8. **Copy the deployment URL** (e.g., `https://your-backend.vercel.app`)

### Deploy Frontend:

1. In Vercel Dashboard, click **"Add New Project"** again
2. Import the same repository: **Bharath2805/eu_bot**
3. Configure:
   - **Framework Preset**: Create React App
   - **Root Directory**: `frontend` (click "Edit" and type `frontend`)
   - **Build Command**: `npm run build` (auto-filled)
   - **Output Directory**: `build` (auto-filled)
4. Click **"Environment Variables"** and add:
   ```
   REACT_APP_API_URL = [your backend URL from above]
   ```
5. Click **"Deploy"**
6. **Copy the frontend URL** (e.g., `https://your-frontend.vercel.app`)

### Update CORS:

1. Go back to **Backend Project** → **Settings** → **Environment Variables**
2. Update `CORS_ORIGINS` to: `https://your-frontend.vercel.app`
3. Go to **Deployments** tab → Click the three dots on latest deployment → **Redeploy**

## 🎉 Done!

Visit your frontend URL and test the chatbot!

---

## Alternative: Deploy via CLI

If you prefer CLI, run these commands (you'll be prompted to login):

```bash
# Deploy Backend
cd backend
vercel

# When prompted:
# - Set up and deploy? Yes
# - Which scope? (select your account)
# - Link to existing project? No
# - Project name? eu-bot-backend
# - Directory? ./
# - Override settings? No

# Add environment variables:
vercel env add OPENAI_API_KEY
vercel env add TAVILY_API_KEY
vercel env add VECTOR_STORE_ID
vercel env add CORS_ORIGINS

# Deploy Frontend (in new terminal)
cd ../frontend
vercel

# Add environment variable:
vercel env add REACT_APP_API_URL
```

