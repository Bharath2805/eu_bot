# Final Setup Steps - Connect Frontend and Backend

## Your Deployed URLs:

✅ **Frontend**: 
- Deployment: `https://eu-bot-frontend-mca9h4d02-bharath-kumar-reddy-s-projects.vercel.app`
- Domain: `https://eu-bot-frontend.vercel.app`

✅ **Backend**: 
- Deployment: `https://eu-pwwoaoq76-bharath-kumar-reddy-s-projects.vercel.app`
- Domain: `https://eu-bot.vercel.app`

## Step 1: Update Frontend Environment Variable

1. Go to Vercel Dashboard: https://vercel.com/dashboard
2. Click on your **frontend project** (`eu-bot-frontend`)
3. Go to **Settings** → **Environment Variables**
4. Find `REACT_APP_API_URL` (or add it if missing)
5. Update the value to: `https://eu-bot.vercel.app`
   (Use the backend domain, not the deployment URL)
6. Make sure it's enabled for **Production**, **Preview**, and **Development**
7. Click **Save**

## Step 2: Redeploy Frontend

1. Go to **Deployments** tab in your frontend project
2. Click the three dots (⋯) on the latest deployment
3. Click **"Redeploy"**
4. Wait for the build to complete (2-3 minutes)

## Step 3: Update Backend CORS

1. Go to your **backend project** (`eu-bot`) in Vercel Dashboard
2. Go to **Settings** → **Environment Variables**
3. Find `CORS_ORIGINS` (or add it if missing)
4. Update the value to: `https://eu-bot-frontend.vercel.app`
   (Use the frontend domain)
5. If you want to allow both domains, use: `https://eu-bot-frontend.vercel.app,https://eu-bot-frontend-mca9h4d02-bharath-kumar-reddy-s-projects.vercel.app`
6. Make sure it's enabled for **Production**, **Preview**, and **Development**
7. Click **Save**

## Step 4: Redeploy Backend

1. Go to **Deployments** tab in your backend project
2. Click the three dots (⋯) on the latest deployment
3. Click **"Redeploy"**
4. Wait for the deployment to complete

## Step 5: Test Your Application

1. Visit your frontend: `https://eu-bot-frontend.vercel.app`
2. Open browser Developer Tools (F12) → Console tab
3. Try sending a message in the chatbot
4. Check for any errors in the console

### Expected Behavior:
- ✅ Chatbot should load
- ✅ Messages should send and receive responses
- ✅ No CORS errors in console
- ✅ File upload should work

### If you see errors:

**CORS Error:**
- Verify `CORS_ORIGINS` in backend includes your frontend URL
- Make sure you redeployed backend after updating

**Connection Error / 404:**
- Verify `REACT_APP_API_URL` in frontend points to backend URL
- Make sure you redeployed frontend after updating
- Check that backend URL is correct: `https://eu-bot.vercel.app`

**API Error:**
- Check backend deployment logs in Vercel
- Verify all environment variables are set in backend:
  - `OPENAI_API_KEY`
  - `TAVILY_API_KEY`
  - `VECTOR_STORE_ID`

## Quick Checklist:

- [ ] Updated `REACT_APP_API_URL` in frontend to `https://eu-bot.vercel.app`
- [ ] Redeployed frontend
- [ ] Updated `CORS_ORIGINS` in backend to `https://eu-bot-frontend.vercel.app`
- [ ] Redeployed backend
- [ ] Tested frontend at `https://eu-bot-frontend.vercel.app`
- [ ] No errors in browser console
- [ ] Chatbot responds to messages

## Your Final URLs:

🌐 **Frontend (User-facing)**: `https://eu-bot-frontend.vercel.app`  
🔧 **Backend API**: `https://eu-bot.vercel.app`

You can share the frontend URL with users!


