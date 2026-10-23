# Setup Email Configuration in AWS Systems Manager Parameter Store
# Run this script after setting up your AWS CLI with proper credentials

Write-Host "Setting up email configuration in AWS Parameter Store..." -ForegroundColor Green

# Set email username (Gmail address)
aws ssm put-parameter `
    --name "/hospital/email-username" `
    --value "shamilmrm2001@gmail.com" `
    --type "SecureString" `
    --description "Hospital Management System Email Username" `
    --overwrite

# Set email password (Gmail app password)
aws ssm put-parameter `
    --name "/hospital/email-password" `
    --value "wqle yhlg iprs ggjg" `
    --type "SecureString" `
    --description "Hospital Management System Email Password" `
    --overwrite

# Set from email address
aws ssm put-parameter `
    --name "/hospital/email-from-address" `
    --value "shamilmrm2001@gmail.com" `
    --type "SecureString" `
    --description "Hospital Management System From Email Address" `
    --overwrite

Write-Host "Email configuration parameters have been set up in AWS Parameter Store!" -ForegroundColor Green
Write-Host ""
Write-Host "Parameters created:" -ForegroundColor Yellow
Write-Host "- /hospital/email-username" -ForegroundColor Cyan
Write-Host "- /hospital/email-password" -ForegroundColor Cyan
Write-Host "- /hospital/email-from-address" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: These are stored as SecureString type for security." -ForegroundColor Yellow
