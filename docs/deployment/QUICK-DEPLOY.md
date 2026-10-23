# 🚀 Quick Deployment Reference

## Prerequisites Checklist
- [ ] AWS Account created (aws.amazon.com/free)
- [ ] AWS CLI installed
- [ ] GitHub account
- [ ] Git installed locally

## 1-Minute Setup Commands

### Install AWS CLI (Windows)
```powershell
# Download and run installer
Invoke-WebRequest -Uri "https://awscli.amazonaws.com/AWSCLIV2.msi" -OutFile "AWSCLIV2.msi"
Start-Process msiexec.exe -Wait -ArgumentList '/I AWSCLIV2.msi /quiet'
```

### Configure AWS
```powershell
aws configure
# Enter: Access Key ID, Secret Key, us-east-1, json
```

### Deploy to AWS
```powershell
# Run setup script
.\setup-aws.bat

# OR run PowerShell script directly
.\deploy-to-aws.ps1
```

## GitHub Setup (5 minutes)

1. Create repository: `hospital-management-system`
2. Push code:
```bash
git remote add origin https://github.com/YOUR-USERNAME/hospital-management-system.git
git push -u origin main
```
3. Add GitHub Secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

## Useful Commands

```powershell
# Check deployment status
aws ecs describe-services --cluster hospital-cluster --services hospital-backend-service

# View logs
aws logs tail /ecs/hospital-backend --follow

# Force redeploy
aws ecs update-service --cluster hospital-cluster --service hospital-backend-service --force-new-deployment

# Check infrastructure
aws cloudformation describe-stacks --stack-name hospital-infrastructure
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| AWS CLI not found | Install from awscli.amazonaws.com |
| Permission denied | Check IAM user has PowerUserAccess |
| Service won't start | Check CloudWatch logs |
| Database connection error | Verify security groups |

## 💰 Free Tier Resources Used

- RDS db.t3.micro (750 hours/month)
- ECS Fargate (20GB storage)
- ALB (750 hours/month)  
- CloudWatch (5GB logs/month)
- ECR (500MB storage/month)

**Total: $0/month** ✅

## 🎯 Success Indicators

- ✅ CloudFormation stack: `CREATE_COMPLETE`
- ✅ ECS services: `RUNNING` (2 tasks)
- ✅ ALB: Health checks passing
- ✅ Application accessible via ALB DNS

## Quick Links

- [Full Deployment Guide](COMPLETE-DEPLOYMENT-GUIDE.md)
- [AWS Console](https://console.aws.amazon.com/)
- [GitHub Actions](https://github.com/YOUR-USERNAME/hospital-management-system/actions)
