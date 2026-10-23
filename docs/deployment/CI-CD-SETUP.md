# Hospital Management System - CI/CD Setup Guide

## 🚀 Setting up GitHub Actions CI/CD Pipeline

Your CI/CD pipeline is now ready! Follow these steps to complete the setup:

### 📋 **Required GitHub Secrets**

You need to add these 4 secrets to your GitHub repository:

1. **AWS_ACCESS_KEY_ID** - Your AWS access key
2. **AWS_SECRET_ACCESS_KEY** - Your AWS secret key  
3. **EC2_SSH_PRIVATE_KEY** - Content of your SSH private key
4. **EC2_HOST** - Your EC2 instance IP (already set to 34.207.201.88)

### 🔑 **Step 1: Get Your AWS Credentials**

Run this command to get your AWS credentials:
```bash
aws sts get-caller-identity
aws configure list
```

Your AWS credentials are typically stored in:
- Windows: `C:\Users\YourUsername\.aws\credentials`
- Linux/Mac: `~/.aws/credentials`

### 🔐 **Step 2: Get Your SSH Private Key Content**

Your SSH key is located at: `C:\Users\Arivanan\hospital-management-system\hospital-key.pem`

To get the content:
```powershell
Get-Content "C:\Users\Arivanan\hospital-management-system\hospital-key.pem" | Out-String
```

### 🛠️ **Step 3: Add Secrets to GitHub**

1. Go to your repository: https://github.com/arivanan0218/hospital-management-system
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret:

   **AWS_ACCESS_KEY_ID**
   ```
   AKIA... (your AWS access key)
   ```

   **AWS_SECRET_ACCESS_KEY**
   ```
   (your AWS secret access key)
   ```

   **EC2_SSH_PRIVATE_KEY**
   ```
   -----BEGIN RSA PRIVATE KEY-----
   (paste the entire content of hospital-key.pem here)
   -----END RSA PRIVATE KEY-----
   ```

   **EC2_HOST**
   ```
   34.207.201.88
   ```

### 🎯 **Step 4: Test the Pipeline**

Once secrets are added, push a change to trigger the pipeline:

```bash
git add .
git commit -m "Setup CI/CD pipeline"
git push origin dev-aws
```

### 🔄 **What the Pipeline Does:**

1. **Test Stage**: Runs Python tests and validates code
2. **Build Stage**: Builds Docker images for frontend and backend
3. **Push Stage**: Pushes images to AWS ECR
4. **Deploy Stage**: Deploys new containers to your EC2 instance
5. **Health Check**: Verifies the deployment is successful

### ✅ **Pipeline Triggers:**

- **Push to `main` branch**: Full deploy to production
- **Push to `dev-aws` branch**: Deploy to your current environment
- **Pull requests**: Run tests only (no deployment)

### 📊 **Monitoring:**

- View pipeline status at: https://github.com/arivanan0218/hospital-management-system/actions
- Check deployment logs in the GitHub Actions tab
- Monitor your application at: http://34.207.201.88/

### 🚨 **Troubleshooting:**

If the pipeline fails:
1. Check the logs in GitHub Actions
2. Verify all secrets are set correctly
3. Ensure your EC2 instance is running
4. Check that AWS credentials have proper permissions

### 🎉 **Success Indicators:**

When working correctly, you'll see:
- ✅ Green checkmarks in GitHub Actions
- Updated containers on your EC2 instance
- Health check passing at http://34.207.201.88/health

---

## 🔄 **Continuous Deployment Workflow:**

1. **Code Changes** → Push to GitHub
2. **Automated Tests** → Validate code quality
3. **Build Images** → Create new Docker containers
4. **Deploy** → Update EC2 instance automatically
5. **Health Check** → Verify deployment success
6. **Live Application** → Users see updates immediately

Your hospital management system now has enterprise-grade CI/CD! 🏥✨
