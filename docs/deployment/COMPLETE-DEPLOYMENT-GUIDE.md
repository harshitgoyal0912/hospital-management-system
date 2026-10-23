# 🏥 Hospital Management System - Complete Deployment & CI/CD Guide

## 📋 Table of Contents

1. [Project Overview](#-project-overview)
2. [Prerequisites](#-prerequisites)
3. [AWS Setup & Configuration](#-aws-setup--configuration)
4. [Local Development Setup](#-local-development-setup)
5. [Docker Configuration](#-docker-configuration)
6. [AWS Infrastructure Deployment](#-aws-infrastructure-deployment)
7. [Application Deployment](#-application-deployment)
8. [CI/CD Pipeline Setup](#-cicd-pipeline-setup)
9. [Monitoring & Maintenance](#-monitoring--maintenance)
10. [Troubleshooting](#-troubleshooting)

---

## 🎯 Project Overview

### What We're Building
- **Hospital Management System** with AI-powered chatbot
- **Backend**: FastAPI with PostgreSQL database
- **Frontend**: React.js with Vite
- **Infrastructure**: AWS EC2 with Docker containers
- **CI/CD**: GitHub Actions with automated deployments
- **Proxy**: Nginx for routing and CORS handling

### Architecture Diagram
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GitHub Repo   │────▶│  GitHub Actions  │────▶│   AWS ECR       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                         │
                                ▼                         │
┌─────────────────┐    ┌──────────────────┐              │
│    End Users    │────▶│  AWS EC2 Instance │◀─────────────┘
└─────────────────┘    └──────────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
            ┌─────────────┐ ┌─────────┐ ┌─────────────┐
            │Nginx Proxy  │ │Frontend │ │Backend+DB   │
            │   :80       │ │  :3000  │ │:8000+:5432  │
            └─────────────┘ └─────────┘ └─────────────┘
```

### Email System Integration
The system includes automatic email notifications for:
- Meeting confirmations and reminders
- Staff notifications
- System alerts and updates

**Email Configuration Required:**
- SMTP server settings (Gmail recommended)
- App-specific passwords for Gmail
- Environment variables for secure credential storage

---

## ✅ Prerequisites

### Required Software
- [ ] **Git** (version 2.30+)
- [ ] **Node.js** (version 18+) 
- [ ] **Python** (version 3.11+)
- [ ] **Docker Desktop** (version 20+)
- [ ] **AWS CLI** (version 2.0+)
- [ ] **VS Code** (recommended)

### Required Accounts
- [ ] **GitHub Account** (free tier sufficient)
- [ ] **AWS Account** (free tier sufficient for this project)
- [ ] **OpenAI Account** (for AI chatbot functionality)

### Knowledge Prerequisites
- Basic understanding of Git/GitHub
- Basic command line usage
- Understanding of web applications (frontend/backend)
- Basic AWS concepts (EC2, Security Groups)

---

## 🔧 AWS Setup & Configuration

### Step 1: Create AWS Account
1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click "Create an AWS Account"
3. Follow the registration process
4. **Important**: Set up billing alerts to avoid unexpected charges

### Step 2: Install AWS CLI

#### Windows (PowerShell):
```powershell
# Download and install AWS CLI v2
Invoke-WebRequest -Uri "https://awscli.amazonaws.com/AWSCLIV2.msi" -OutFile "AWSCLIV2.msi"
Start-Process msiexec.exe -Wait -ArgumentList '/I AWSCLIV2.msi /quiet'
Remove-Item "AWSCLIV2.msi"

# Verify installation
aws --version
```

#### Linux/Mac:
```bash
# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Mac
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
```

### Step 3: Create IAM User for Deployment

1. **Log in to AWS Console** → IAM → Users → "Create User"
2. **Username**: `hospital-deployment-user`
3. **Attach Policies**:
   ```json
   - AmazonEC2FullAccess
   - AmazonECRFullAccess
   - IAMReadOnlyAccess
   ```
4. **Create Access Key**:
   - Go to Security Credentials
   - Create Access Key → "Application running outside AWS"
   - **Save the credentials securely**

### Step 4: Configure AWS CLI
```bash
aws configure
# AWS Access Key ID: [your-access-key]
# AWS Secret Access Key: [your-secret-key]
# Default region name: us-east-1
# Default output format: json

# Test configuration
aws sts get-caller-identity
```

---

## 💻 Local Development Setup

### Step 1: Clone Repository
```bash
git clone https://github.com/your-username/hospital-management-system.git
cd hospital-management-system
```

### Step 2: Backend Setup
```bash
cd backend-python

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install uv
uv pip install -e .

# Test backend
python main.py
```

### Step 3: Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Step 4: Database Setup (Local Testing)
```bash
# Start PostgreSQL with Docker
docker run -d \
  --name hospital-postgres-local \
  -e POSTGRES_DB=hospital_db \
  -e POSTGRES_USER=hospital_user \
  -e POSTGRES_PASSWORD=hospital_pass \
  -p 5432:5432 \
  postgres:15-alpine

# Test database connection
cd backend-python
python setup_database.py
```

### Step 5: Email Configuration Setup

The system requires email configuration for meeting confirmations and notifications.

#### Gmail Setup (Recommended)
1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate app password for "Mail"
   - Save the 16-character password

#### Environment Variables
Create `.env` file in `backend-python/` directory:
```bash
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password-here
EMAIL_FROM_NAME=Hospital Management System
EMAIL_FROM_ADDRESS=your-email@gmail.com

# Other configurations...
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=postgresql://hospital_user:hospital_pass@localhost:5432/hospital_db
```

#### Test Email Configuration
```bash
cd backend-python
python ../test-email-config.py
```

**Expected Output:**
```
Testing Email Configuration...
==================================================
SMTP Server: smtp.gmail.com
SMTP Port: 587
Email Username: your-email@gmail.com
From Email: your-email@gmail.com
Password Set: Yes

Connecting to SMTP server...
Starting TLS encryption...
Logging in...
Sending test email...

✅ SUCCESS: Test email sent successfully!
Check your inbox at: your-email@gmail.com
```

---

## 🐳 Docker Configuration

### Backend Dockerfile
Create `backend-python/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install uv && uv pip install --system -e .

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["./start.sh"]
```

### Frontend Dockerfile
Create `frontend/Dockerfile`:
```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM node:20-alpine

WORKDIR /app
RUN npm install -g serve
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

COPY --from=builder /app/dist ./dist
RUN chown -R nextjs:nodejs /app

USER nextjs

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

CMD ["serve", "-s", "dist", "-l", "3000"]
```

### Test Docker Builds
```bash
# Build backend
cd backend-python
docker build -t hospital-backend .

# Build frontend  
cd frontend
docker build -t hospital-frontend .

# Test containers
docker run -p 8000:8000 hospital-backend
docker run -p 3000:3000 hospital-frontend
```

---

## ☁️ AWS Infrastructure Deployment

### Step 1: Create ECR Repositories
```bash
# Create repositories for storing Docker images
aws ecr create-repository --repository-name hospital-backend --region us-east-1
aws ecr create-repository --repository-name hospital-frontend --region us-east-1

# Get login credentials
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin [ACCOUNT-ID].dkr.ecr.us-east-1.amazonaws.com
```

### Step 2: Create EC2 Key Pair
```bash
# Create SSH key pair
aws ec2 create-key-pair --key-name hospital-key --query 'KeyMaterial' --output text > hospital-key.pem

# Set correct permissions
chmod 600 hospital-key.pem
```

### Step 3: Deploy EC2 Instance

Create `deploy-infrastructure.ps1`:
```powershell
# Create security group
$securityGroupId = aws ec2 create-security-group `
  --group-name hospital-sg `
  --description "Hospital Management System Security Group" `
  --query 'GroupId' --output text

# Add security group rules
aws ec2 authorize-security-group-ingress --group-id $securityGroupId --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $securityGroupId --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $securityGroupId --protocol tcp --port 443 --cidr 0.0.0.0/0

# Create EC2 instance
$userData = @"
#!/bin/bash
apt-get update
apt-get install -y docker.io awscli curl

# Start Docker
systemctl start docker
systemctl enable docker
usermod -aG docker ubuntu

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create Docker network
docker network create hospital-network

# Configure AWS CLI
mkdir -p /home/ubuntu/.aws
echo "[default]" > /home/ubuntu/.aws/config
echo "region = us-east-1" >> /home/ubuntu/.aws/config
chown -R ubuntu:ubuntu /home/ubuntu/.aws
"@

$userDataBase64 = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($userData))

$instanceId = aws ec2 run-instances `
  --image-id ami-0e731c8a588258d0d `
  --count 1 `
  --instance-type t3.micro `
  --key-name hospital-key `
  --security-group-ids $securityGroupId `
  --user-data $userDataBase64 `
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=hospital-management-server}]' `
  --query 'Instances[0].InstanceId' --output text

Write-Host "Instance ID: $instanceId"

# Wait for instance to be running
aws ec2 wait instance-running --instance-ids $instanceId

# Get public IP
$publicIp = aws ec2 describe-instances --instance-ids $instanceId --query 'Reservations[0].Instances[0].PublicIpAddress' --output text

Write-Host "Public IP: $publicIp"
Write-Host "SSH Command: ssh -i hospital-key.pem ubuntu@$publicIp"
```

Run the deployment:
```powershell
./deploy-infrastructure.ps1
```

---

## � Email Configuration for Deployment

Before deploying to AWS, ensure email functionality is properly configured for both Docker and AWS ECS deployments.

### Step 1: Setup Environment Variables for Docker

Create `.env` file in the root directory (alongside `docker-compose.yml`):

```bash
# Google Gemini API Key (required for AI features)
GEMINI_API_KEY=your_gemini_api_key_here

# Email Configuration for SMTP
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
EMAIL_FROM_NAME=Hospital Management System
EMAIL_FROM_ADDRESS=your-email@gmail.com

# Frontend API Keys (if needed)
VITE_CLAUDE_API_KEY=your_claude_api_key_here
VITE_OPENAI_API_KEY=your_openai_api_key_here
VITE_GROQ_API_KEY=your_groq_api_key_here
VITE_GOOGLE_API_KEY=your_google_api_key_here
```

### Step 2: Setup AWS Parameter Store for ECS (Production)

Run the setup script to store email credentials securely in AWS:

```bash
# Make sure AWS CLI is configured with proper permissions
aws configure

# Run the email parameter setup script
./setup-email-aws-params.ps1
```

This script creates the following AWS Systems Manager parameters:
- `/hospital/email-username` (SecureString)
- `/hospital/email-password` (SecureString) 
- `/hospital/email-from-address` (SecureString)

### Step 3: Test Email Configuration

```bash
# Test locally with Docker
python test-email-config.py

# Test in Docker container
docker-compose up backend
docker exec -it hospital_backend python ../test-email-config.py
```

### Step 4: Verify Deployment Configuration

The following files have been updated with email support:

**Docker Compose (`docker-compose.yml`):**
- Added email environment variables to backend service
- Variables are read from root `.env` file

**ECS Task Definition (`backend-task-definition.json`):**
- Added email environment variables 
- Sensitive credentials stored as AWS Parameter Store secrets
- Non-sensitive settings (SMTP server, port) as environment variables

**Common Issues & Solutions:**

1. **Gmail App Password Required:**
   - Must use App Password, not regular Gmail password
   - Enable 2-Factor Authentication first
   
2. **Docker Environment Variables:**
   - Ensure `.env` file is in root directory (not backend-python)
   - Check variable names match exactly
   
3. **AWS Parameter Store Access:**
   - ECS task role needs `ssm:GetParameter` permission
   - Parameter names must match task definition exactly

---

## �🚀 Application Deployment

### Step 1: Build and Push Images
```bash
# Get your account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build and push backend
cd backend-python
docker build -t $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/hospital-backend:latest .
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/hospital-backend:latest

# Build and push frontend
cd ../frontend
docker build -t $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/hospital-frontend:latest .
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/hospital-frontend:latest
```

### Step 2: Deploy to EC2

Create `deploy-to-ec2.sh`:
```bash
#!/bin/bash
set -e

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🚀 Starting deployment to EC2..."

# Login to ECR
aws ecr get-login-password --region us-east-1 | sudo docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Clean up old containers and images
echo "🧹 Cleaning up old resources..."
sudo docker system prune -f
sudo docker volume prune -f
sudo docker image prune -f

# Pull latest images
echo "📥 Pulling latest images..."
sudo docker pull $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/hospital-backend:latest
sudo docker pull $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/hospital-frontend:latest

# Stop and remove old containers (keep database and nginx)
echo "🛑 Stopping old containers..."
sudo docker stop hospital-backend hospital-frontend 2>/dev/null || true
sudo docker rm hospital-backend hospital-frontend 2>/dev/null || true

# Start database if not running
if ! sudo docker ps | grep -q hospital-postgres; then
  echo "🗄️ Starting PostgreSQL database..."
  sudo docker run -d \
    --name hospital-postgres \
    --network hospital-network \
    --restart unless-stopped \
    -e POSTGRES_DB=hospital_db \
    -e POSTGRES_USER=hospital_user \
    -e POSTGRES_PASSWORD=hospital_pass \
    -p 5432:5432 \
    postgres:15-alpine
  
  sleep 30  # Wait for database to be ready
fi

# Start backend container
echo "🔄 Starting new backend container..."
sudo docker run -d \
  --name hospital-backend \
  --network hospital-network \
  --restart unless-stopped \
  -e DATABASE_URL="postgresql://hospital_user:hospital_pass@hospital-postgres:5432/hospital_db" \
  -p 8000:8000 \
  $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/hospital-backend:latest

# Start frontend container
echo "🔄 Starting new frontend container..."
sudo docker run -d \
  --name hospital-frontend \
  --network hospital-network \
  --restart unless-stopped \
  $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/hospital-frontend:latest

# Start nginx proxy if not running
if ! sudo docker ps | grep -q nginx-proxy; then
  echo "🌐 Starting Nginx proxy..."
  
  # Create nginx configuration
  cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server hospital-backend:8000;
    }
    
    upstream frontend {
        server hospital-frontend:3000;
    }

    server {
        listen 80;
        
        # Backend API routes
        location /health {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            add_header Access-Control-Allow-Origin *;
        }
        
        location /docs {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            add_header Access-Control-Allow-Origin *;
        }
        
        location /tools/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            add_header Access-Control-Allow-Origin *;
        }
        
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            add_header Access-Control-Allow-Origin *;
        }
        
        # Frontend routes (catch-all)
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
EOF

  sudo docker run -d \
    --name nginx-proxy \
    --network hospital-network \
    --restart unless-stopped \
    -p 80:80 \
    -v $(pwd)/nginx.conf:/etc/nginx/nginx.conf:ro \
    nginx:alpine
fi

# Wait for containers to be healthy
echo "⏳ Waiting for containers to be healthy..."
sleep 30

# Test health endpoint
echo "🧪 Testing application health..."
if curl -f http://localhost/health >/dev/null 2>&1; then
  echo "✅ Deployment successful! Application is healthy."
  echo "🌐 Application URL: http://$(curl -s http://checkip.amazonaws.com)/"
else
  echo "❌ Deployment failed! Health check failed."
  exit 1
fi

# Show container status
echo "📋 Container status:"
sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo "🎉 Deployment completed successfully!"
```

Copy and run the deployment script:
```bash
# Copy to EC2
scp -i hospital-key.pem deploy-to-ec2.sh ubuntu@[EC2-PUBLIC-IP]:~/

# Execute on EC2
ssh -i hospital-key.pem ubuntu@[EC2-PUBLIC-IP] "chmod +x deploy-to-ec2.sh && ./deploy-to-ec2.sh"
```

---

## 🔄 CI/CD Pipeline Setup

### Step 1: Create GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:
```yaml
name: Hospital Management System CI/CD

on:
  push:
    branches: [ main, dev-aws ]
  pull_request:
    branches: [ main ]

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY_BACKEND: hospital-backend
  ECR_REPOSITORY_FRONTEND: hospital-frontend
  EC2_HOST: YOUR_EC2_PUBLIC_IP  # Update this

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd backend-python
        pip install uv
        uv pip install --system -e .
    
    - name: Run basic health check
      run: |
        cd backend-python
        python -c "import database; print('✅ Database module imported successfully')"

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/dev-aws'
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}

    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v2

    - name: Build and push backend image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        echo "🔨 Building backend image..."
        cd backend-python
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY_BACKEND:$IMAGE_TAG .
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY_BACKEND:latest .
        echo "📤 Pushing backend image..."
        docker push $ECR_REGISTRY/$ECR_REPOSITORY_BACKEND:$IMAGE_TAG
        docker push $ECR_REGISTRY/$ECR_REPOSITORY_BACKEND:latest
        echo "✅ Backend image pushed successfully"

    - name: Build and push frontend image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        echo "🔨 Building frontend image..."
        cd frontend
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY_FRONTEND:$IMAGE_TAG .
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY_FRONTEND:latest .
        echo "📤 Pushing frontend image..."
        docker push $ECR_REGISTRY/$ECR_REPOSITORY_FRONTEND:$IMAGE_TAG
        docker push $ECR_REGISTRY/$ECR_REPOSITORY_FRONTEND:latest
        echo "✅ Frontend image pushed successfully"

    - name: Create deployment script
      run: |
        cat > deploy-to-ec2.sh << 'EOF'
        #!/bin/bash
        set -e
        
        echo "🚀 Starting deployment to EC2..."
        
        # Configure AWS CLI on EC2
        aws configure set region us-east-1
        
        # Login to ECR
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        aws ecr get-login-password --region us-east-1 | sudo docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
        
        # Clean up old resources
        echo "🧹 Cleaning up old resources..."
        sudo docker system prune -f
        sudo docker volume prune -f
        sudo docker image prune -f
        
        # Pull latest images
        echo "📥 Pulling latest images..."
        sudo docker pull $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/hospital-backend:latest
        sudo docker pull $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/hospital-frontend:latest
        
        # Stop and remove old containers (except database and nginx)
        echo "🛑 Stopping old containers..."
        sudo docker stop hospital-backend hospital-frontend 2>/dev/null || true
        sudo docker rm hospital-backend hospital-frontend 2>/dev/null || true
        
        # Start new backend container
        echo "🔄 Starting new backend container..."
        sudo docker run -d \
          --name hospital-backend \
          --network hospital-network \
          --restart unless-stopped \
          -e DATABASE_URL="postgresql://hospital_user:hospital_pass@hospital-postgres:5432/hospital_db" \
          $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/hospital-backend:latest
        
        # Start new frontend container
        echo "🔄 Starting new frontend container..."
        sudo docker run -d \
          --name hospital-frontend \
          --network hospital-network \
          --restart unless-stopped \
          $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/hospital-frontend:latest
        
        # Wait for containers to be healthy
        echo "⏳ Waiting for containers to be healthy..."
        sleep 30
        
        # Test health endpoint
        echo "🧪 Testing application health..."
        if curl -f http://localhost/health >/dev/null 2>&1; then
          echo "✅ Deployment successful! Application is healthy."
        else
          echo "❌ Deployment failed! Health check failed."
          exit 1
        fi
        
        # Show container status
        echo "📋 Container status:"
        sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        
        echo "🎉 Deployment completed successfully!"
        echo "🌐 Application URL: http://${{ env.EC2_HOST }}/"
        EOF
        
        chmod +x deploy-to-ec2.sh

    - name: Deploy to EC2
      env:
        PRIVATE_KEY: ${{ secrets.EC2_SSH_PRIVATE_KEY }}
        HOST: ${{ env.EC2_HOST }}
        USER: ubuntu
      run: |
        echo "🔐 Setting up SSH..."
        echo "$PRIVATE_KEY" > private_key.pem
        chmod 600 private_key.pem
        
        echo "📁 Copying deployment script to EC2..."
        scp -i private_key.pem -o StrictHostKeyChecking=no deploy-to-ec2.sh $USER@$HOST:~/
        
        echo "🚀 Executing deployment on EC2..."
        ssh -i private_key.pem -o StrictHostKeyChecking=no $USER@$HOST '
          chmod +x ~/deploy-to-ec2.sh
          ~/deploy-to-ec2.sh
        '
        
        echo "🧹 Cleaning up..."
        rm -f private_key.pem

    - name: Final health check
      run: |
        echo "🔍 Final health check..."
        sleep 10
        if curl -f http://${{ env.EC2_HOST }}/health; then
          echo ""
          echo "🎉 ✅ DEPLOYMENT SUCCESSFUL! ✅ 🎉"
          echo "🌐 Your Hospital Management System is live at: http://${{ env.EC2_HOST }}/"
          echo "🏥 Health API: http://${{ env.EC2_HOST }}/health"
          echo "📚 Documentation: http://${{ env.EC2_HOST }}/docs"
        else
          echo "❌ Final health check failed"
          exit 1
        fi
```

### Step 2: Set Up GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

#### AWS_ACCESS_KEY_ID
```
Your AWS access key from IAM user creation
```

#### AWS_SECRET_ACCESS_KEY  
```
Your AWS secret key from IAM user creation
```

#### EC2_SSH_PRIVATE_KEY
```
-----BEGIN RSA PRIVATE KEY-----
[Content of your hospital-key.pem file]
-----END RSA PRIVATE KEY-----
```

#### EC2_HOST
```
Your EC2 public IP address
```

### Step 3: Test CI/CD Pipeline

```bash
# Make any change and push
git add .
git commit -m "Test CI/CD pipeline"
git push origin main

# Monitor the pipeline at:
# https://github.com/your-username/hospital-management-system/actions
```

---

## 📊 Monitoring & Maintenance

### Health Monitoring Script

Create `monitor-health.sh`:
```bash
#!/bin/bash

HEALTH_URL="http://YOUR_EC2_IP/health"
SLACK_WEBHOOK="your-slack-webhook-url"  # Optional

check_health() {
    response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)
    
    if [ $response -eq 200 ]; then
        echo "✅ $(date): Application is healthy"
        return 0
    else
        echo "❌ $(date): Application is unhealthy (HTTP $response)"
        # Send alert to Slack (optional)
        if [ ! -z "$SLACK_WEBHOOK" ]; then
            curl -X POST -H 'Content-type: application/json' \
                --data '{"text":"🚨 Hospital Management System is down!"}' \
                $SLACK_WEBHOOK
        fi
        return 1
    fi
}

# Run health check
check_health

# Set up cron job for continuous monitoring
# Add to crontab: */5 * * * * /path/to/monitor-health.sh >> /var/log/hospital-health.log 2>&1
```

### Log Monitoring

```bash
# View application logs
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker logs hospital-backend --tail 50"
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker logs hospital-frontend --tail 50"
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker logs nginx-proxy --tail 50"

# Monitor system resources
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "top"
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "df -h"
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "free -h"
```

### Backup Strategy

Create `backup-database.sh`:
```bash
#!/bin/bash

BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
sudo docker exec hospital-postgres pg_dump -U hospital_user hospital_db > $BACKUP_DIR/hospital_db_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/hospital_db_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "✅ Database backup completed: hospital_db_$DATE.sql.gz"

# Optional: Upload to S3
# aws s3 cp $BACKUP_DIR/hospital_db_$DATE.sql.gz s3://your-backup-bucket/database/
```

---

## 🔧 Troubleshooting

### Common Issues & Solutions

#### 1. CI/CD Pipeline Failures

**Issue**: "The security token included in the request is invalid"
```bash
# Solution: Update AWS credentials in GitHub secrets
aws sts get-caller-identity  # Test locally
# Then update AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY secrets
```

**Issue**: "no space left on device"
```bash
# Solution: Clean up Docker resources
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP
sudo docker system prune -a -f
sudo docker volume prune -f
```

#### 2. Application Not Loading

**Issue**: Website shows "This site can't be reached"
```bash
# Check security group allows port 80
aws ec2 describe-security-groups --group-ids YOUR_SG_ID

# Check nginx is running
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker ps | grep nginx"
```

**Issue**: Backend API errors
```bash
# Check backend logs
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker logs hospital-backend"

# Check database connection
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker exec hospital-backend curl http://localhost:8000/health"
```

#### 3. Database Connection Issues

**Issue**: "password authentication failed for user postgres"
```bash
# Check database credentials
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker logs hospital-postgres"

# Restart backend with correct credentials
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "
sudo docker stop hospital-backend
sudo docker rm hospital-backend
sudo docker run -d --name hospital-backend --network hospital-network --restart unless-stopped -e DATABASE_URL='postgresql://hospital_user:hospital_pass@hospital-postgres:5432/hospital_db' [YOUR_ECR_REGISTRY]/hospital-backend:latest
"
```

#### 4. SSH Connection Issues

**Issue**: "Permission denied (publickey)"
```bash
# Fix key permissions
chmod 600 hospital-key.pem

# Verify key format
head -1 hospital-key.pem  # Should show: -----BEGIN RSA PRIVATE KEY-----
```

**Issue**: "WARNING: UNPROTECTED PRIVATE KEY FILE"
```bash
# In WSL, copy key to Linux filesystem
cp hospital-key.pem ~/hospital-key.pem
chmod 600 ~/hospital-key.pem
ssh -i ~/hospital-key.pem ubuntu@YOUR_EC2_IP
```

### Emergency Recovery Procedures

#### Complete System Recovery
```bash
# 1. Stop all containers
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker stop \$(sudo docker ps -aq)"

# 2. Remove all containers except database
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker rm hospital-backend hospital-frontend nginx-proxy"

# 3. Clean Docker system
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker system prune -a -f"

# 4. Redeploy using CI/CD
git commit --allow-empty -m "Emergency redeploy"
git push origin main
```

#### Database Recovery
```bash
# 1. Restore from backup
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "
gunzip /home/ubuntu/backups/hospital_db_YYYYMMDD_HHMMSS.sql.gz
sudo docker exec -i hospital-postgres psql -U hospital_user hospital_db < /home/ubuntu/backups/hospital_db_YYYYMMDD_HHMMSS.sql
"
```

---

## 🎯 Best Practices & Security

### Security Checklist

- [ ] **AWS IAM**: Use least-privilege access
- [ ] **SSH Keys**: Secure with proper permissions (600)
- [ ] **Secrets**: Never commit to Git, use GitHub Secrets
- [ ] **Database**: Use strong passwords, not exposed publicly
- [ ] **HTTPS**: Set up SSL certificates for production
- [ ] **Firewall**: Restrict security groups to necessary ports
- [ ] **Updates**: Regularly update dependencies and base images

### Performance Optimization

- [ ] **Database Indexing**: Add indexes for common queries
- [ ] **Docker Images**: Use multi-stage builds to reduce size
- [ ] **Nginx**: Enable gzip compression
- [ ] **Monitoring**: Set up CloudWatch for AWS resources
- [ ] **CDN**: Consider CloudFront for static assets

### Scaling Considerations

- [ ] **Load Balancer**: Add ALB for multiple EC2 instances
- [ ] **Auto Scaling**: Set up Auto Scaling Groups
- [ ] **Database**: Consider RDS for managed PostgreSQL
- [ ] **Container Orchestration**: Migrate to ECS or EKS
- [ ] **Monitoring**: Implement comprehensive logging and metrics

---

## 📝 Summary

You now have:

✅ **Complete Infrastructure**: EC2, ECR, Security Groups  
✅ **Dockerized Application**: Backend, Frontend, Database, Nginx  
✅ **CI/CD Pipeline**: Automated testing and deployment  
✅ **Monitoring**: Health checks and logging  
✅ **Security**: IAM users, SSH keys, secrets management  
✅ **Maintenance**: Backup and recovery procedures  

### Next Steps

1. **Custom Domain**: Set up Route 53 and SSL certificates
2. **Monitoring**: Add CloudWatch dashboards
3. **Scaling**: Implement load balancing and auto-scaling
4. **Testing**: Add comprehensive test suites
5. **Documentation**: Create user guides and API documentation

### Support & Resources

- **AWS Documentation**: https://docs.aws.amazon.com/
- **Docker Documentation**: https://docs.docker.com/
- **GitHub Actions**: https://docs.github.com/en/actions
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/

---

**🎉 Congratulations!** You have successfully deployed a production-ready Hospital Management System with complete CI/CD pipeline on AWS!

Your application is now live at: **http://YOUR_EC2_IP/**

---

*Last Updated: August 2025*  
*Version: 1.0*
