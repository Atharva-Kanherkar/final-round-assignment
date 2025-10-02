# Deploy to Digital Ocean - Step by Step

## What You'll Get

- **Live API** at: `https://your-app.ondigitalocean.app`
- **PostgreSQL Database** (managed, automatic backups)
- **Auto-scaling** if traffic increases
- **SSL certificate** (HTTPS) automatically configured
- **API Documentation** at: `https://your-app.ondigitalocean.app/api/docs`

**Cost**: $27/month (~7 months with your $200 credit)

---

## Step-by-Step Deployment

### Step 1: Log into Digital Ocean

Go to: https://cloud.digitalocean.com

### Step 2: Create App

1. Click **"Create"** (top right)
2. Select **"App Platform"**

### Step 3: Connect GitHub

1. Select **"GitHub"**
2. Click **"Manage Access"**
3. Authorize Digital Ocean to access your GitHub
4. Select repository: **"Atharva-Kanherkar/final-round-assignment"**
5. Select branch: **"main"**
6. Click **"Next"**

### Step 4: Configure Resources

Digital Ocean will auto-detect:
- **Source**: Dockerfile
- **Build Command**: Auto-detected
- **Run Command**: From Dockerfile

**Verify these settings**:
- Resource Type: **Web Service**
- Instance Size: **Basic (512MB RAM, $5/month)** or **Professional XS ($12/month)** ← Choose this one
- HTTP Port: **8000**

Click **"Next"**

### Step 5: Add Database

1. Click **"Add Resource"** → **"Database"**
2. Select **"PostgreSQL"**
3. Version: **16**
4. Size: **Basic (1GB RAM, $15/month)**
5. Database name: **interview-db**
6. Click **"Add Database"**

**Important**: Check the box **"Trust sources in this app"**

Click **"Next"**

### Step 6: Set Environment Variables

Click **"Edit"** next to your app component

Add these environment variables:

```
Name: OPENAI_API_KEY
Value: sk-your-actual-openai-key-here
Encrypt: ✓ (check this box)

Name: MODEL_NAME
Value: gpt-4o

Name: LOG_LEVEL
Value: INFO

Name: WORKERS
Value: 2
```

**DATABASE_URL will be auto-added by Digital Ocean when you added the database**

Click **"Save"**

### Step 7: Configure Health Check

Under **"Health Checks"**:
- HTTP Path: `/api/ping`
- Port: `8000`
- Initial Delay: `10` seconds
- Period: `30` seconds

Click **"Next"**

### Step 8: Name Your App

- App Name: **interview-api** (or whatever you want)
- Region: **New York** (or closest to you)

### Step 9: Review and Deploy

1. Review the summary
2. **Monthly cost should show ~$27** ($12 app + $15 database)
3. Click **"Create Resources"**

### Step 10: Wait for Deployment

- Deployment takes **5-10 minutes**
- Watch the build logs in the dashboard
- Status will change to **"Deployed"** when ready

---

## After Deployment

### 1. Get Your API URL

In the App Platform dashboard, you'll see:
```
https://interview-api-xxxxx.ondigitalocean.app
```

Copy this URL.

### 2. Test the API

```bash
# Health check
curl https://your-app.ondigitalocean.app/api/ping

# Should return:
{"status":"ok","timestamp":"..."}
```

### 3. View API Documentation

Open in browser:
```
https://your-app.ondigitalocean.app/api/docs
```

You'll see interactive Swagger UI!

### 4. Test Creating a Session

```bash
curl -X POST https://your-app.ondigitalocean.app/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "John Doe\nSoftware Engineer\n5 years experience\nSkills: Python, AWS, Docker, Kubernetes\nEducation: BS Computer Science, State University\nExperience:\n- TechCorp (2020-2023): Backend development with microservices\n- StartupXYZ (2018-2020): Full-stack development",
    "job_description_text": "Senior Backend Engineer\nCompany: TechCo\nRequirements:\n- 5+ years Python experience\n- Strong system design skills\n- AWS/Cloud experience\n- Docker and Kubernetes\nResponsibilities:\n- Design scalable backend services\n- Lead technical initiatives\n- Mentor junior engineers"
  }'
```

You should get back a session ID and first question!

---

## Monitoring

### View Logs

1. In App Platform dashboard
2. Click your app
3. Go to **"Runtime Logs"**
4. See real-time logs

### View Database

1. Click **"interview-db"** in your app
2. Go to **"Connection Details"**
3. Can connect via `psql` or any PostgreSQL client

### Check Metrics

Dashboard shows:
- CPU usage
- Memory usage
- Request count
- Response times

---

## Troubleshooting

### Build Fails

**Check**:
1. Build logs in dashboard
2. Verify Dockerfile is correct
3. Check all files pushed to GitHub

**Fix**: Usually auto-resolves on retry. Click "Force Rebuild"

### App Crashes on Start

**Check Runtime Logs for**:
- Database connection errors
- Missing environment variables
- Migration failures

**Fix**:
1. Verify `OPENAI_API_KEY` is set
2. Check `DATABASE_URL` is auto-configured
3. Restart app from dashboard

### Database Connection Failed

**Check**:
- Database is in same region as app
- "Trust sources" is checked
- DATABASE_URL environment variable exists

**Fix**: Re-add database to app or check connection settings

---

## Cost Breakdown

| Resource | Plan | Cost/Month |
|----------|------|------------|
| App (API Server) | Professional XS | $12 |
| PostgreSQL Database | Basic 1GB | $15 |
| **Total** | | **$27** |

**With $200 credit**: **7.4 months free**

To reduce costs:
- Use Basic app tier ($5) instead of Professional → Total $20/month
- Pause app when not needed → $0 while paused

---

## Success Checklist

After deployment, verify:

- [ ] App status shows "Deployed" (green)
- [ ] Health check passes: `curl https://your-app.../api/ping`
- [ ] API docs accessible: `https://your-app.../api/docs`
- [ ] Database connected (check logs for "Database initialized")
- [ ] Can create session via POST /api/sessions
- [ ] No errors in runtime logs

---

## Next Steps After Deployment

1. **Test the API** using Swagger UI at `/api/docs`
2. **Share the URL** with interviewers
3. **Build frontend** (optional) - Next.js can call this API

---

## If Something Goes Wrong

**Contact me with**:
1. Screenshot of error from Runtime Logs
2. Build logs if build failed
3. I'll help debug

---

**Deployment should take 10-15 minutes total.**

**Everything is ready - go deploy!**
