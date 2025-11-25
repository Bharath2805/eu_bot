# Deploy Frontend to Vercel - Step by Step

## Your Backend URL
✅ Backend deployed at: `https://eu-cuhs5x2tn-bharath-kumar-reddy-s-projects.vercel.app`

## Deploy Frontend (Follow These Exact Steps)

### Step 1: Go to Vercel Dashboard
1. Open https://vercel.com/dashboard
2. Make sure you're logged in

### Step 2: Import Repository Again
1. Click the **"Add New..."** button (top right)
2. Select **"Project"** (not "Team" or other options)
3. You'll see a list of your GitHub repositories
4. Find **"Bharath2805/eu_bot"** in the list
5. Click **"Import"** next to it

### Step 3: Configure Frontend Project
After clicking Import, you'll see the configuration page:

1. **Project Name**: Change it to something like `eu-bot-frontend` (to distinguish from backend)

2. **Framework Preset**: 
   - Click the dropdown
   - Select **"Create React App"** (it should auto-detect, but if not, select it manually)

3. **Root Directory** (IMPORTANT!):
   - Click **"Edit"** next to Root Directory
   - Change from `.` to `frontend`
   - Press Enter or click outside

4. **Build and Output Settings** (should auto-fill, but verify):
   - Build Command: `npm run build` (or `cd frontend && npm run build`)
   - Output Directory: `build` (or `frontend/build`)
   - Install Command: `npm install` (or `cd frontend && npm install`)

### Step 4: Add Environment Variable
1. Scroll down to **"Environment Variables"** section
2. Click **"Add"** or the **"+"** button
3. Add this variable:
   - **Key**: `REACT_APP_API_URL`
   - **Value**: `https://eu-cuhs5x2tn-bharath-kumar-reddy-s-projects.vercel.app`
   - **Environment**: Select all (Production, Preview, Development)
4. Click **"Save"**

### Step 5: Deploy
1. Scroll to the bottom
2. Click **"Deploy"** button
3. Wait for the build to complete (usually 2-3 minutes)

### Step 6: Get Frontend URL
After deployment completes:
1. You'll see a success message
2. Copy the deployment URL (e.g., `https://eu-bot-frontend.vercel.app`)

### Step 7: Update Backend CORS
1. Go back to your **backend project** in Vercel dashboard
2. Click on the backend project name
3. Go to **Settings** → **Environment Variables**
4. Find `CORS_ORIGINS` variable
5. Click **"Edit"** or update it to: `https://your-frontend-url.vercel.app`
   (Replace with your actual frontend URL from Step 6)
6. Go to **Deployments** tab
7. Click the three dots (⋯) on the latest deployment
8. Click **"Redeploy"**

## Troubleshooting

### If you don't see "New Project" button:
- Make sure you're on the main dashboard (not inside a project)
- Look for "Add New..." or "+" button in the top right

### If the repository doesn't appear:
- Make sure you've pushed all code to GitHub
- Try refreshing the page
- Check that you're logged into the correct GitHub account in Vercel

### If build fails:
- Check the build logs in Vercel
- Make sure `package.json` is in the `frontend` directory
- Verify Root Directory is set to `frontend`

### If frontend can't connect to backend:
- Verify `REACT_APP_API_URL` is set correctly
- Make sure backend URL doesn't have a trailing slash
- Check browser console for CORS errors
- Update `CORS_ORIGINS` in backend environment variables

## Quick Checklist
- [ ] Imported `Bharath2805/eu_bot` repository
- [ ] Set Root Directory to `frontend`
- [ ] Framework set to "Create React App"
- [ ] Added `REACT_APP_API_URL` environment variable with backend URL
- [ ] Deployed successfully
- [ ] Updated `CORS_ORIGINS` in backend with frontend URL
- [ ] Redeployed backend

