# Simple EC2 Deployment for Testing

Write-Host "Hospital Management System - Simple EC2 Deployment" -ForegroundColor Green
Write-Host "==================================================="

$ACCOUNT_ID = "324037286635"
$AWS_REGION = "us-east-1"
$VPC_ID = "vpc-02b9cb42b900c1742"
$SUBNET1 = "subnet-07c708f6f5f6e4b8b"

# Create key pair for EC2 access
Write-Host "Creating EC2 key pair..." -ForegroundColor Yellow
try {
    aws ec2 create-key-pair --key-name hospital-key --query 'KeyMaterial' --output text --region $AWS_REGION | Out-File -FilePath "hospital-key.pem" -Encoding ascii
    Write-Host "Key pair created: hospital-key.pem" -ForegroundColor Green
    Write-Host "IMPORTANT: Save this file securely - you'll need it to access your server" -ForegroundColor Red
} catch {
    Write-Host "Key pair already exists or error occurred" -ForegroundColor Yellow
}

# Create security group for EC2
Write-Host "Creating security group..." -ForegroundColor Yellow
try {
    $SG_ID = aws ec2 create-security-group --group-name hospital-web-sg --description "Hospital Web Security Group" --vpc-id $VPC_ID --query 'GroupId' --output text --region $AWS_REGION
    
    # Allow HTTP, SSH and custom ports
    aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr 0.0.0.0/0 --region $AWS_REGION
    aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $AWS_REGION
    aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region $AWS_REGION
    aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 3000 --cidr 0.0.0.0/0 --region $AWS_REGION
    
    Write-Host "Security group created: $SG_ID" -ForegroundColor Green
} catch {
    $SG_ID = aws ec2 describe-security-groups --filters "Name=group-name,Values=hospital-web-sg" --query 'SecurityGroups[0].GroupId' --output text --region $AWS_REGION
    Write-Host "Using existing security group: $SG_ID" -ForegroundColor Yellow
}

# Create user data script for EC2 instance
$USER_DATA = @"
#!/bin/bash
yum update -y
yum install -y docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install docker-compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Pull and run backend
docker run -d --name hospital-backend -p 8000:8000 -e DATABASE_URL=sqlite:///./hospital.db $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/hospital-backend:latest

# Pull and run frontend  
docker run -d --name hospital-frontend -p 3000:3000 $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/hospital-frontend:latest

# Create a simple nginx reverse proxy
cat > /etc/nginx/nginx.conf << 'EOF'
events {}
http {
    upstream backend {
        server localhost:8000;
    }
    upstream frontend {
        server localhost:3000;
    }
    
    server {
        listen 80;
        
        location /api/ {
            proxy_pass http://backend/;
        }
        
        location / {
            proxy_pass http://frontend/;
        }
    }
}
EOF

yum install -y nginx
systemctl start nginx
systemctl enable nginx
"@

$USER_DATA_ENCODED = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($USER_DATA))

# Launch EC2 instance
Write-Host "Launching EC2 instance..." -ForegroundColor Yellow
$INSTANCE_ID = aws ec2 run-instances `
    --image-id ami-0c7217cdde317cfec `
    --count 1 `
    --instance-type t3.micro `
    --key-name hospital-key `
    --security-group-ids $SG_ID `
    --subnet-id $SUBNET1 `
    --user-data $USER_DATA_ENCODED `
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=hospital-web-server}]' `
    --query 'Instances[0].InstanceId' `
    --output text `
    --region $AWS_REGION

Write-Host "EC2 instance launched: $INSTANCE_ID" -ForegroundColor Green

# Wait for instance to be running
Write-Host "Waiting for instance to start..." -ForegroundColor Yellow
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $AWS_REGION

# Get public IP
$PUBLIC_IP = aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].PublicIpAddress' --output text --region $AWS_REGION

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "EC2 Deployment Complete!" -ForegroundColor Green  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Instance ID: $INSTANCE_ID" -ForegroundColor Yellow
Write-Host "Public IP: $PUBLIC_IP" -ForegroundColor Yellow
Write-Host ""
Write-Host "Your Hospital Management System will be available at:" -ForegroundColor Green
Write-Host "- Full Application: http://$PUBLIC_IP" -ForegroundColor Green
Write-Host "- Backend API: http://$PUBLIC_IP:8000" -ForegroundColor Green  
Write-Host "- Frontend: http://$PUBLIC_IP:3000" -ForegroundColor Green
Write-Host "- Backend Health: http://$PUBLIC_IP:8000/health" -ForegroundColor Green
Write-Host ""
Write-Host "Note: It may take 2-3 minutes for the containers to start after instance launch" -ForegroundColor Yellow
Write-Host ""
Write-Host "To SSH into your server:" -ForegroundColor Cyan
Write-Host "ssh -i hospital-key.pem ec2-user@$PUBLIC_IP" -ForegroundColor White
Write-Host ""
Write-Host "To check container status on the server:" -ForegroundColor Cyan
Write-Host "docker ps" -ForegroundColor White
Write-Host "docker logs hospital-backend" -ForegroundColor White
Write-Host "docker logs hospital-frontend" -ForegroundColor White
