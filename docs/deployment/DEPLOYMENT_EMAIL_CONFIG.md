# 🚀 DEPLOYMENT EMAIL CONFIGURATION GUIDE

## 📧 **Your Email Configuration**
Based on your `.env` file, here are your email settings:

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=shamilmrm2001@gmail.com
EMAIL_PASSWORD=wqle yhlg iprs ggjg
EMAIL_FROM_NAME=Hospital Management System
EMAIL_FROM_ADDRESS=shamilmrm2001@gmail.com
```

## 🔧 **DEPLOYMENT METHODS**

### **1. Docker Deployment (Recommended)**

#### **Option A: Docker Compose** ✅
Your `docker-compose.yml` is already configured! Just run:

```bash
cd "E:\Rise Ai\Hospital Management System\hospital-management-system"
docker-compose up -d
```

The email environment variables are already defined in your `docker-compose.yml`:
```yaml
environment:
  - SMTP_SERVER=${SMTP_SERVER}
  - SMTP_PORT=${SMTP_PORT}
  - EMAIL_USERNAME=${EMAIL_USERNAME}
  - EMAIL_PASSWORD=${EMAIL_PASSWORD}
  - EMAIL_FROM_NAME=${EMAIL_FROM_NAME}
  - EMAIL_FROM_ADDRESS=${EMAIL_FROM_ADDRESS}
```

#### **Option B: Docker Run Command**
```bash
docker run -d \
  --name hospital-backend \
  -p 8000:8000 \
  -e SMTP_SERVER=smtp.gmail.com \
  -e SMTP_PORT=587 \
  -e EMAIL_USERNAME=shamilmrm2001@gmail.com \
  -e EMAIL_PASSWORD="wqle yhlg iprs ggjg" \
  -e EMAIL_FROM_NAME="Hospital Management System" \
  -e EMAIL_FROM_ADDRESS=shamilmrm2001@gmail.com \
  hospital-backend:latest
```

---

### **2. GitHub Actions Deployment** 🚀

Your GitHub Actions workflow needs these secrets configured. Go to your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

Add these secrets:
```
Name: EMAIL_USERNAME
Value: shamilmrm2001@gmail.com

Name: EMAIL_PASSWORD  
Value: wqle yhlg iprs ggjg

Name: EMAIL_FROM_NAME
Value: Hospital Management System

Name: EMAIL_FROM_ADDRESS
Value: shamilmrm2001@gmail.com

Name: SMTP_SERVER
Value: smtp.gmail.com

Name: SMTP_PORT
Value: 587
```

Update your `.github/workflows/deploy.yml` to include email environment variables:

```yaml
env:
  # Add these email variables to your existing env section
  SMTP_SERVER: ${{ secrets.SMTP_SERVER }}
  SMTP_PORT: ${{ secrets.SMTP_PORT }}
  EMAIL_USERNAME: ${{ secrets.EMAIL_USERNAME }}
  EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
  EMAIL_FROM_NAME: ${{ secrets.EMAIL_FROM_NAME }}
  EMAIL_FROM_ADDRESS: ${{ secrets.EMAIL_FROM_ADDRESS }}
```

---

### **3. AWS Deployment** ☁️

#### **ECS Task Definition**
Add to your task definition JSON:

```json
{
  "environment": [
    {"name": "SMTP_SERVER", "value": "smtp.gmail.com"},
    {"name": "SMTP_PORT", "value": "587"},
    {"name": "EMAIL_USERNAME", "value": "shamilmrm2001@gmail.com"},
    {"name": "EMAIL_PASSWORD", "value": "wqle yhlg iprs ggjg"},
    {"name": "EMAIL_FROM_NAME", "value": "Hospital Management System"},
    {"name": "EMAIL_FROM_ADDRESS", "value": "shamilmrm2001@gmail.com"}
  ]
}
```

#### **EC2 Deployment**
```bash
# SSH into your EC2 instance and run:
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export EMAIL_USERNAME=shamilmrm2001@gmail.com
export EMAIL_PASSWORD="wqle yhlg iprs ggjg"
export EMAIL_FROM_NAME="Hospital Management System"
export EMAIL_FROM_ADDRESS=shamilmrm2001@gmail.com

# Then start your application
```

---

### **4. Heroku Deployment** 🟪

```bash
heroku config:set SMTP_SERVER=smtp.gmail.com
heroku config:set SMTP_PORT=587
heroku config:set EMAIL_USERNAME=shamilmrm2001@gmail.com
heroku config:set EMAIL_PASSWORD="wqle yhlg iprs ggjg"
heroku config:set EMAIL_FROM_NAME="Hospital Management System"
heroku config:set EMAIL_FROM_ADDRESS=shamilmrm2001@gmail.com
```

---

### **5. Kubernetes Deployment** ☸️

Create a secret and configmap:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: hospital-email-secret
type: Opaque
stringData:
  EMAIL_PASSWORD: "wqle yhlg iprs ggjg"
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: hospital-email-config
data:
  SMTP_SERVER: "smtp.gmail.com"
  SMTP_PORT: "587"
  EMAIL_USERNAME: "shamilmrm2001@gmail.com"
  EMAIL_FROM_NAME: "Hospital Management System"
  EMAIL_FROM_ADDRESS: "shamilmrm2001@gmail.com"
```

Reference in your deployment:
```yaml
spec:
  containers:
  - name: hospital-backend
    envFrom:
    - configMapRef:
        name: hospital-email-config
    - secretRef:
        name: hospital-email-secret
```

---

## 🧪 **TESTING YOUR DEPLOYMENT**

### **Quick Test Commands**

1. **Check Environment Variables:**
```bash
# In your deployed container/server:
echo $EMAIL_USERNAME
echo $SMTP_SERVER
```

2. **Test Email Configuration:**
```bash
# Run this in your deployment environment:
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('EMAIL_USERNAME:', os.getenv('EMAIL_USERNAME'))
print('SMTP_SERVER:', os.getenv('SMTP_SERVER'))
print('Password configured:', 'Yes' if os.getenv('EMAIL_PASSWORD') else 'No')
"
```

3. **Test Email Sending:**
```bash
# Use your diagnostic tool:
python diagnose_email_deployment.py
```

---

## 🎯 **COMMON ISSUES & SOLUTIONS**

### **Issue 1: "Email credentials not configured"**
**Solution:** Environment variables not loaded
- Ensure `.env` file exists in deployment
- Or set environment variables directly

### **Issue 2: "SMTP Authentication failed"**  
**Solution:** Gmail App Password issues
- Verify App Password: `wqle yhlg iprs ggjg`
- Enable 2-Factor Authentication on Gmail
- Re-generate App Password if needed

### **Issue 3: "Network/Firewall blocking SMTP"**
**Solution:** Port 587 blocked
- Use port 465 (SSL) instead of 587 (TLS)
- Configure firewall to allow SMTP ports

### **Issue 4: "Works locally but not in deployment"**
**Solution:** Environment loading differences
- Local: `.env` file automatically loaded
- Deployment: Must explicitly set environment variables

---

## ✅ **VERIFICATION CHECKLIST**

- [ ] Environment variables set in deployment
- [ ] Gmail App Password working
- [ ] Port 587 accessible from deployment server
- [ ] No firewall blocking SMTP
- [ ] Test email sent successfully

---

## 🚀 **NEXT STEPS**

1. **Choose your deployment method** from above
2. **Configure environment variables** using the appropriate method
3. **Test email functionality** using the diagnostic tools
4. **Schedule a meeting** to verify email notifications work

---

## 💡 **PRO TIP**

Your Docker Compose setup is already correctly configured! If you're using Docker, just make sure your `.env` file is in the same directory as `docker-compose.yml` and run:

```bash
docker-compose up -d
```

This should work immediately with email notifications! 🎉
