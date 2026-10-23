# 🚀 GitHub Secrets Setup for Email Configuration
# PowerShell script to guide you through setting up GitHub secrets

Write-Host "🔐 GITHUB SECRETS SETUP GUIDE" -ForegroundColor Green
Write-Host "================================="
Write-Host ""
Write-Host "Go to your GitHub repository:" -ForegroundColor Yellow
Write-Host "Settings → Secrets and variables → Actions → New repository secret" -ForegroundColor Yellow
Write-Host ""
Write-Host "Add these secrets one by one:" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Secret Name: " -NoNewline -ForegroundColor White
Write-Host "SMTP_SERVER" -ForegroundColor Green
Write-Host "   Secret Value: " -NoNewline -ForegroundColor White  
Write-Host "smtp.gmail.com" -ForegroundColor Yellow
Write-Host ""

Write-Host "2. Secret Name: " -NoNewline -ForegroundColor White
Write-Host "SMTP_PORT" -ForegroundColor Green
Write-Host "   Secret Value: " -NoNewline -ForegroundColor White
Write-Host "587" -ForegroundColor Yellow
Write-Host ""

Write-Host "3. Secret Name: " -NoNewline -ForegroundColor White
Write-Host "EMAIL_USERNAME" -ForegroundColor Green
Write-Host "   Secret Value: " -NoNewline -ForegroundColor White
Write-Host "shamilmrm2001@gmail.com" -ForegroundColor Yellow
Write-Host ""

Write-Host "4. Secret Name: " -NoNewline -ForegroundColor White
Write-Host "EMAIL_PASSWORD" -ForegroundColor Green  
Write-Host "   Secret Value: " -NoNewline -ForegroundColor White
Write-Host "wqle yhlg iprs ggjg" -ForegroundColor Yellow
Write-Host ""

Write-Host "5. Secret Name: " -NoNewline -ForegroundColor White
Write-Host "EMAIL_FROM_NAME" -ForegroundColor Green
Write-Host "   Secret Value: " -NoNewline -ForegroundColor White
Write-Host "Hospital Management System" -ForegroundColor Yellow
Write-Host ""

Write-Host "6. Secret Name: " -NoNewline -ForegroundColor White
Write-Host "EMAIL_FROM_ADDRESS" -ForegroundColor Green
Write-Host "   Secret Value: " -NoNewline -ForegroundColor White
Write-Host "shamilmrm2001@gmail.com" -ForegroundColor Yellow
Write-Host ""

Write-Host "✅ After adding all secrets, your GitHub Actions will have email functionality!" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 Push your code to trigger deployment:" -ForegroundColor Cyan
Write-Host "git add ." -ForegroundColor White
Write-Host "git commit -m 'Add email configuration for deployment'" -ForegroundColor White
Write-Host "git push origin main" -ForegroundColor White
Write-Host ""

Write-Host "📧 To verify email works after deployment, run:" -ForegroundColor Magenta
Write-Host 'curl -X POST http://54.85.118.65/tools/call -H "Content-Type: application/json" -d "{\"params\": {\"name\": \"send_email\", \"arguments\": {\"to_emails\": \"shamilmrm2001@gmail.com\", \"subject\": \"Deployment Test\", \"message\": \"Email working in deployment!\"}}}"' -ForegroundColor White
