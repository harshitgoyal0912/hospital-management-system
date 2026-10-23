# Quick Deploy - Use existing ECR and create minimal infrastructure

Write-Host "Hospital Management System - Quick Deploy" -ForegroundColor Green
Write-Host "==========================================="

$ACCOUNT_ID = aws sts get-caller-identity --query Account --output text
$AWS_REGION = "us-east-1"

Write-Host "Account ID: $ACCOUNT_ID" -ForegroundColor Green
Write-Host "Region: $AWS_REGION" -ForegroundColor Green

# Check if we can use existing infrastructure
Write-Host ""
Write-Host "Checking existing infrastructure..." -ForegroundColor Yellow

# Check for existing VPC with our name
$VPC_ID = aws ec2 describe-vpcs --filters "Name=tag:Name,Values=hospital-vpc" --query 'Vpcs[0].VpcId' --output text --region $AWS_REGION

if ($VPC_ID -eq "None") {
    Write-Host "No existing VPC found. Creating new infrastructure..." -ForegroundColor Yellow
    
    # Create VPC
    $VPC_ID = aws ec2 create-vpc --cidr-block 10.0.0.0/16 --query 'Vpc.VpcId' --output text --region $AWS_REGION
    aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames --region $AWS_REGION
    aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support --region $AWS_REGION
    aws ec2 create-tags --resources $VPC_ID --tags Key=Name,Value=hospital-vpc --region $AWS_REGION
    
    Write-Host "VPC created: $VPC_ID" -ForegroundColor Green
    
    # Create Internet Gateway
    $IGW_ID = aws ec2 create-internet-gateway --query 'InternetGateway.InternetGatewayId' --output text --region $AWS_REGION
    aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID --region $AWS_REGION
    aws ec2 create-tags --resources $IGW_ID --tags Key=Name,Value=hospital-igw --region $AWS_REGION
    
    # Create subnets
    $SUBNET1_ID = aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 --availability-zone us-east-1a --query 'Subnet.SubnetId' --output text --region $AWS_REGION
    $SUBNET2_ID = aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.2.0/24 --availability-zone us-east-1b --query 'Subnet.SubnetId' --output text --region $AWS_REGION
    
    aws ec2 modify-subnet-attribute --subnet-id $SUBNET1_ID --map-public-ip-on-launch --region $AWS_REGION
    aws ec2 modify-subnet-attribute --subnet-id $SUBNET2_ID --map-public-ip-on-launch --region $AWS_REGION
    
    aws ec2 create-tags --resources $SUBNET1_ID --tags Key=Name,Value=hospital-public-1 --region $AWS_REGION
    aws ec2 create-tags --resources $SUBNET2_ID --tags Key=Name,Value=hospital-public-2 --region $AWS_REGION
    
    # Create route table
    $RT_ID = aws ec2 create-route-table --vpc-id $VPC_ID --query 'RouteTable.RouteTableId' --output text --region $AWS_REGION
    aws ec2 create-route --route-table-id $RT_ID --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID --region $AWS_REGION
    aws ec2 associate-route-table --subnet-id $SUBNET1_ID --route-table-id $RT_ID --region $AWS_REGION
    aws ec2 associate-route-table --subnet-id $SUBNET2_ID --route-table-id $RT_ID --region $AWS_REGION
    
    Write-Host "Networking created" -ForegroundColor Green
} else {
    Write-Host "Using existing VPC: $VPC_ID" -ForegroundColor Green
    
    # Get existing subnets
    $SUBNETS = aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[?MapPublicIpOnLaunch==`true`].SubnetId' --output text --region $AWS_REGION
    $SUBNET_ARRAY = $SUBNETS -split "`t"
    $SUBNET1_ID = $SUBNET_ARRAY[0]
    $SUBNET2_ID = $SUBNET_ARRAY[1]
    
    Write-Host "Using existing subnets: $SUBNET1_ID, $SUBNET2_ID" -ForegroundColor Green
}

# Build and push Docker images
Write-Host ""
Write-Host "Building and pushing Docker images..." -ForegroundColor Yellow

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and push backend
Write-Host "Building backend image..." -ForegroundColor Yellow
cd backend-python
docker build -t hospital-backend .
docker tag hospital-backend:latest $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/hospital-backend:latest
docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/hospital-backend:latest
cd ..

# Build and push frontend
Write-Host "Building frontend image..." -ForegroundColor Yellow
cd frontend
docker build -t hospital-frontend .
docker tag hospital-frontend:latest $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/hospital-frontend:latest
docker push $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/hospital-frontend:latest
cd ..

Write-Host "Docker images pushed successfully!" -ForegroundColor Green

# Create ECS cluster if it doesn't exist
try {
    aws ecs describe-clusters --clusters hospital-cluster --region $AWS_REGION | Out-Null
    Write-Host "Using existing ECS cluster" -ForegroundColor Green
} catch {
    aws ecs create-cluster --cluster-name hospital-cluster --region $AWS_REGION
    Write-Host "ECS cluster created" -ForegroundColor Green
}

# Create task execution role if it doesn't exist
$ROLE_NAME = "ecsTaskExecutionRole"
try {
    $ROLE_ARN = aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text
    Write-Host "Using existing task execution role" -ForegroundColor Green
} catch {
    # Create the role
    $TRUST_POLICY = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
"@
    
    $TRUST_POLICY | Out-File -FilePath "trust-policy.json" -Encoding utf8
    aws iam create-role --role-name $ROLE_NAME --assume-role-policy-document file://trust-policy.json
    aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
    Remove-Item "trust-policy.json"
    
    $ROLE_ARN = aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text
    Write-Host "Task execution role created" -ForegroundColor Green
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Quick Deploy Complete!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Images built and pushed to ECR!" -ForegroundColor Green
Write-Host "VPC: $VPC_ID"
Write-Host "Subnets: $SUBNET1_ID, $SUBNET2_ID"
Write-Host "Task Role: $ROLE_ARN"
Write-Host ""
Write-Host "Next: Create a simple ECS service to test your deployment" -ForegroundColor Yellow
Write-Host "Your Docker images are now available at:"
Write-Host "- Backend: $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/hospital-backend:latest"
Write-Host "- Frontend: $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/hospital-frontend:latest"
