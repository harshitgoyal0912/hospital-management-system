# 🚀 Hospital Management System - Quick Reference Guide

## Daily Operations Cheat Sheet

### 🔍 Check System Status
```bash
# Health check
curl http://YOUR_EC2_IP/health

# Container status
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker ps"

# System resources
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "df -h && free -h"
```

### 📝 View Logs
```bash
# Backend logs (last 50 lines)
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker logs hospital-backend --tail 50"

# Frontend logs
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker logs hospital-frontend --tail 50"

# Nginx logs
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker logs nginx-proxy --tail 50"

# Follow live logs
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker logs -f hospital-backend"
```

### 🔄 Deploy Changes
```bash
# Method 1: CI/CD Pipeline (Recommended)
git add .
git commit -m "Your changes description"
git push origin main  # Triggers automatic deployment

# Method 2: Manual Deploy
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "./deploy-to-ec2.sh"
```

### 🧹 Maintenance Commands
```bash
# Clean up disk space
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "
sudo docker system prune -f
sudo docker volume prune -f
sudo docker image prune -f
"

# Restart specific service
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "
sudo docker restart hospital-backend
sudo docker restart hospital-frontend
sudo docker restart nginx-proxy
"

# Update containers with latest images
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "
ACCOUNT_ID=\$(aws sts get-caller-identity --query Account --output text)
aws ecr get-login-password --region us-east-1 | sudo docker login --username AWS --password-stdin \$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
sudo docker pull \$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/hospital-backend:latest
sudo docker pull \$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/hospital-frontend:latest
"
```

### 🗄️ Database Operations
```bash
# Connect to database
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker exec -it hospital-postgres psql -U hospital_user -d hospital_db"

# Backup database
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "
sudo docker exec hospital-postgres pg_dump -U hospital_user hospital_db > backup_\$(date +%Y%m%d_%H%M%S).sql
"

# View database size
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "
sudo docker exec hospital-postgres psql -U hospital_user -d hospital_db -c \"
SELECT pg_size_pretty(pg_database_size('hospital_db'));
\"
"
```

### 🔧 Troubleshooting
```bash
# Check if services are responding
curl -I http://YOUR_EC2_IP/health
curl -I http://YOUR_EC2_IP/docs
curl -I http://YOUR_EC2_IP/

# Check container health
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker inspect hospital-backend | grep Health -A 10"

# View container resource usage
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker stats --no-stream"

# Check network connectivity between containers
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "
sudo docker exec hospital-backend ping hospital-postgres -c 3
sudo docker exec hospital-frontend ping hospital-backend -c 3
"
```

### 📊 Monitoring URLs
- **Application**: http://YOUR_EC2_IP/
- **Health Check**: http://YOUR_EC2_IP/health
- **API Documentation**: http://YOUR_EC2_IP/docs
- **GitHub Actions**: https://github.com/your-username/hospital-management-system/actions

### 🚨 Emergency Procedures

#### Application Down
```bash
# 1. Check all containers
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker ps -a"

# 2. Restart all services
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "
sudo docker restart hospital-postgres
sleep 10
sudo docker restart hospital-backend
sleep 5
sudo docker restart hospital-frontend
sudo docker restart nginx-proxy
"

# 3. If still failing, redeploy
git commit --allow-empty -m "Emergency redeploy"
git push origin main
```

#### Out of Disk Space
```bash
# 1. Clean Docker resources
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "
sudo docker system prune -a -f
sudo docker volume prune -f
sudo docker container prune -f
sudo docker image prune -a -f
"

# 2. Clean system logs
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "
sudo journalctl --vacuum-time=7d
sudo find /var/log -name '*.log' -mtime +7 -delete
"
```

#### Database Issues
```bash
# 1. Check database status
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker logs hospital-postgres --tail 20"

# 2. Restart database
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "
sudo docker restart hospital-postgres
sleep 30
sudo docker restart hospital-backend
"

# 3. Check database connectivity
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "
sudo docker exec hospital-backend curl http://localhost:8000/health
"
```

### 📱 Mobile Monitoring Script

Create `mobile-check.sh` for quick mobile monitoring:
```bash
#!/bin/bash
echo "🏥 Hospital Management System Status"
echo "=================================="
echo "⏰ $(date)"
echo ""

# Health check
if curl -s http://YOUR_EC2_IP/health | grep -q "healthy"; then
    echo "✅ Application: HEALTHY"
else
    echo "❌ Application: UNHEALTHY"
fi

# Check if accessible
if curl -s -o /dev/null -w "%{http_code}" http://YOUR_EC2_IP/ | grep -q "200"; then
    echo "✅ Website: ACCESSIBLE"
else
    echo "❌ Website: NOT ACCESSIBLE"
fi

echo ""
echo "🔗 Quick Links:"
echo "📱 App: http://YOUR_EC2_IP/"
echo "🩺 Health: http://YOUR_EC2_IP/health"
echo "📚 Docs: http://YOUR_EC2_IP/docs"
```

### 🎯 Performance Optimization Tips

```bash
# Monitor response times
curl -w "@curl-format.txt" -o /dev/null -s http://YOUR_EC2_IP/health

# Create curl-format.txt:
echo "     time_namelookup:  %{time_namelookup}\\n
        time_connect:  %{time_connect}\\n
     time_appconnect:  %{time_appconnect}\\n
    time_pretransfer:  %{time_pretransfer}\\n
       time_redirect:  %{time_redirect}\\n
  time_starttransfer:  %{time_starttransfer}\\n
                     ----------\\n
          time_total:  %{time_total}\\n" > curl-format.txt

# Monitor container performance
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker stats --format 'table {{.Container}}\\t{{.CPUPerc}}\\t{{.MemUsage}}\\t{{.NetIO}}'"
```

---

## 🎉 Quick Win Commands

### One-Command Deploy
```bash
git add . && git commit -m "Deploy: $(date)" && git push origin main
```

### One-Command Health Check
```bash
curl -s http://YOUR_EC2_IP/health | jq '.' 2>/dev/null || curl -s http://YOUR_EC2_IP/health
```

### One-Command Log Review
```bash
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "sudo docker logs hospital-backend --tail 20 && echo '---' && sudo docker logs hospital-frontend --tail 20"
```

### One-Command System Status
```bash
ssh -i hospital-key.pem ubuntu@YOUR_EC2_IP "echo 'Containers:' && sudo docker ps --format 'table {{.Names}}\\t{{.Status}}' && echo '\\nResources:' && df -h / && free -h"
```

---

**💡 Pro Tip**: Bookmark this page and replace `YOUR_EC2_IP` with your actual EC2 IP address for quick copy-paste commands!

**🏥 Your Hospital Management System**: http://YOUR_EC2_IP/
