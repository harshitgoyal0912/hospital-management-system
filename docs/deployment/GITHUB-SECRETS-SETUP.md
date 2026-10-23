# GitHub Secrets Configuration Guide

This guide explains how to configure GitHub Secrets for the Hospital Management System to work with the automated CI/CD pipeline.

## Required GitHub Secrets

To deploy the Hospital Management System using GitHub Actions, you need to configure the following secrets in your GitHub repository:

### API Keys & Configuration

1. **VITE_OPENAI_API_KEY** (Required)
   - Description: OpenAI API key for AI-powered features
   - How to get: Go to [OpenAI Platform](https://platform.openai.com/api-keys) and create a new API key
   - Format: `sk-...` (starts with "sk-")
   - Example: `sk-1234567890abcdef1234567890abcdef`

2. **VITE_LANGSMITH_API_KEY** (Optional)
   - Description: LangSmith API key for AI debugging and tracing
   - How to get: Sign up at [LangSmith](https://smith.langchain.com/) and get your API key
   - Format: `lsv2_pt_...`

3. **VITE_MCP_BRIDGE_URL** (Optional)
   - Description: MCP Bridge URL for local development
   - Default: `http://localhost:8080`
   - Production: Set to your deployed MCP bridge URL

### AWS Configuration (For AWS Deployment)

4. **AWS_ACCESS_KEY_ID** (Required for AWS deployment)
   - Description: AWS Access Key ID for ECR and ECS access
   - How to get: Create an IAM user in AWS Console with ECR and ECS permissions

5. **AWS_SECRET_ACCESS_KEY** (Required for AWS deployment)
   - Description: AWS Secret Access Key
   - How to get: Generated when creating AWS Access Key

6. **AWS_REGION** (Optional)
   - Description: AWS region for deployment
   - Default: `us-east-1`

7. **EC2_SSH_PRIVATE_KEY** (Required for EC2 deployment)
   - Description: SSH private key for EC2 instance access
   - How to get: Use the private key file (.pem) for your EC2 instance

## How to Set Up GitHub Secrets

1. Go to your GitHub repository
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add each secret with the name and value as described above

### Step-by-Step Setup

#### 1. OpenAI API Key (Most Important)
```bash
Name: VITE_OPENAI_API_KEY
Value: sk-your-actual-openai-api-key-here
```

#### 2. LangSmith API Key (Optional)
```bash
Name: VITE_LANGSMITH_API_KEY
Value: lsv2_pt_your-langsmith-key-here
```

#### 3. AWS Credentials (For AWS deployment)
```bash
Name: AWS_ACCESS_KEY_ID
Value: AKIA...

Name: AWS_SECRET_ACCESS_KEY
Value: your-secret-access-key

Name: AWS_REGION
Value: us-east-1
```

## Environment File Structure

The GitHub Actions workflow will automatically create a `.env` file in the frontend directory with the following structure:

```env
VITE_OPENAI_API_KEY=sk-your-api-key
VITE_LANGSMITH_API_KEY=lsv2_pt_your-key
VITE_LANGSMITH_PROJECT=hospital-management-system
VITE_LANGSMITH_TRACING=true
VITE_MCP_BRIDGE_URL=http://localhost:8080
```

## Security Best Practices

1. **Never commit API keys** to your repository
2. **Use repository secrets** for sensitive information
3. **Rotate API keys regularly** for security
4. **Limit API key permissions** to only what's needed
5. **Monitor API key usage** in your provider dashboards

## Local Development

For local development, create a `.env` file in the `frontend` directory:

```bash
cd frontend
cp .env.example .env
# Edit .env and add your API keys
```

## Verification

After setting up the secrets:

1. Push code to the `main` branch
2. Check the Actions tab in GitHub
3. Verify the workflow runs successfully
4. Check the deployment logs for any API key related errors

## Troubleshooting

### Common Issues

1. **API Key Not Found Error**
   - Check that `VITE_OPENAI_API_KEY` is set in GitHub Secrets
   - Verify the API key format starts with `sk-`

2. **Authentication Failed**
   - Verify the API key is valid and active
   - Check API key permissions in OpenAI dashboard

3. **Build Failed**
   - Check the GitHub Actions logs
   - Verify all required secrets are configured

4. **Environment Variables Not Available**
   - Ensure secrets are named exactly as shown above
   - Check that secrets are set at the repository level, not organization level

## Support

If you encounter issues:

1. Check the GitHub Actions logs for detailed error messages
2. Verify all secrets are correctly configured
3. Test your API keys manually using the OpenAI API
4. Contact the development team for assistance

## Update Process

When updating API keys:

1. Update the secret value in GitHub repository settings
2. Re-run the GitHub Actions workflow
3. The new API key will be automatically deployed

---

**Note**: The frontend application will now automatically use the API key from environment variables, eliminating the need for manual API key input during user authentication.
