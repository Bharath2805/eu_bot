# Vercel Deployment Instructions

This guide will help you deploy your EU AI Act Compliance Bot to Vercel.

## Prerequisites

1. A GitHub account with your repository: `github.com/Bharath2805/eu_bot`
2. A Vercel account (sign up at https://vercel.com)
3. Your API keys:
   - OpenAI API Key
   - Tavily API Key

## Deployment Steps

### Step 1: Prepare Your Repository

1. Make sure all your changes are committed and pushed to GitHub:
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

### Step 2: Deploy Backend to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New Project"**
3. Import your GitHub repository: `Bharath2805/eu_bot`
4. Configure the project:
   - **Framework Preset**: Other
   - **Root Directory**: `backend`
   - **Build Command**: Leave empty (or `pip install -r requirements.txt`)
   - **Output Directory**: Leave empty
   - **Install Command**: Leave empty

5. **Add Environment Variables** (click "Environment Variables"):
   - `OPENAI_API_KEY` = Your OpenAI API key
   - `TAVILY_API_KEY` = Your Tavily API key
   - `VECTOR_STORE_ID` = `vs_692180726b908191af2f182b14342882`
   - `CORS_ORIGINS` = `https://your-frontend-domain.vercel.app` (you'll update this after deploying frontend)

6. Click **"Deploy"**

7. **Note the backend URL** (e.g., `https://your-backend.vercel.app`)

### Step 3: Deploy Frontend to Vercel

1. In Vercel Dashboard, click **"Add New Project"** again
2. Import the same repository: `Bharath2805/eu_bot`
3. Configure the project:
   - **Framework Preset**: Create React App
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (auto-filled)
   - **Output Directory**: `build` (auto-filled)
   - **Install Command**: `npm install` (auto-filled)

4. **Add Environment Variables**:
   - `REACT_APP_API_URL` = Your backend URL from Step 2 (e.g., `https://your-backend.vercel.app`)

5. Click **"Deploy"**

6. **Note the frontend URL** (e.g., `https://your-frontend.vercel.app`)

### Step 4: Update CORS Settings

1. Go back to your **backend project** in Vercel
2. Go to **Settings** → **Environment Variables**
3. Update `CORS_ORIGINS` to include your frontend URL:
   ```
   https://your-frontend.vercel.app
   ```
   (Or if you want to allow both localhost and production:
   ```
   http://localhost:3000,https://your-frontend.vercel.app
   ```

4. **Redeploy** the backend (go to Deployments → click the three dots → Redeploy)

### Step 5: Verify Deployment

1. Visit your frontend URL
2. Test the chatbot functionality
3. Check browser console for any errors
4. Test file upload functionality

## Important Notes

- **Recommended Approach**: Deploy frontend and backend as **separate Vercel projects** (Steps 2-4 above). This is easier to manage and debug.
- The root `vercel.json` is provided for reference but separate deployments are recommended.
- Each deployment will get its own URL, which you'll use to connect them.

## Environment Variables Summary

### Backend Required Variables:
- `OPENAI_API_KEY` - Your OpenAI API key
- `TAVILY_API_KEY` - Your Tavily API key
- `VECTOR_STORE_ID` - Vector store ID (default: `vs_692180726b908191af2f182b14342882`)
- `CORS_ORIGINS` - Comma-separated list of allowed origins

### Frontend Required Variables:
- `REACT_APP_API_URL` - Your backend API URL

## Troubleshooting

### Backend Issues:
- **500 Errors**: Check that all environment variables are set correctly
- **CORS Errors**: Verify `CORS_ORIGINS` includes your frontend URL
- **Import Errors**: Ensure `requirements.txt` includes all dependencies

### Frontend Issues:
- **API Connection Errors**: Verify `REACT_APP_API_URL` is set correctly
- **Build Errors**: Check that all dependencies are in `package.json`
- **Blank Page**: Check browser console for errors

### Common Solutions:
1. **Clear Vercel cache**: Settings → Clear Build Cache → Redeploy
2. **Check logs**: Vercel Dashboard → Your Project → Deployments → Click on deployment → View Function Logs
3. **Verify environment variables**: Settings → Environment Variables

## Local Development

For local development, create a `.env` file in the root directory:

```bash
# Backend
OPENAI_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
VECTOR_STORE_ID=vs_692180726b908191af2f182b14342882
CORS_ORIGINS=http://localhost:3000

# Frontend (create .env in frontend directory)
REACT_APP_API_URL=http://localhost:8000
```

**Important**: Never commit `.env` files to Git. They are already in `.gitignore`.

## Support

If you encounter issues:
1. Check Vercel deployment logs
2. Verify all environment variables are set
3. Ensure your GitHub repository is up to date
4. Check that both frontend and backend URLs are correct

