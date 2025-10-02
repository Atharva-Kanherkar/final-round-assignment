# Deploy Frontend to Vercel

## Your Backend API
https://orca-app-jubw8.ondigitalocean.app

## Step-by-Step Deployment

### Step 1: Go to Vercel

https://vercel.com

Sign in with GitHub

### Step 2: Import Project

1. Click **"Add New..."** → **"Project"**
2. Select repository: **"Atharva-Kanherkar/final-round-assignment"**
3. Click **"Import"**

### Step 3: Configure Project

**Framework Preset**: Next.js (auto-detected)

**Root Directory**: Click **"Edit"** and set to: `frontend`

**Build Settings** (auto-filled):
- Build Command: `npm run build`
- Output Directory: `.next`
- Install Command: `npm install`

### Step 4: Add Environment Variable

Click **"Environment Variables"**

Add:
```
Name: NEXT_PUBLIC_API_URL
Value: https://orca-app-jubw8.ondigitalocean.app
```

### Step 5: Deploy

Click **"Deploy"**

Wait 2-3 minutes.

### Step 6: Get Your URL

You'll get:
```
https://final-round-assignment-xxxxx.vercel.app
```

---

## Test Your Frontend

1. Open your Vercel URL
2. Click "Load Sample Data"
3. Click "Start Interview"
4. Answer questions
5. See real-time evaluation
6. Complete interview for final report

---

## If Build Fails

**Check**:
- Root directory is set to `frontend`
- Environment variable `NEXT_PUBLIC_API_URL` is set

**Fix**:
- Go to project settings
- Update root directory
- Redeploy

---

## Local Testing (Optional)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

---

**Deployment takes 2-3 minutes. Your frontend will be live!**
