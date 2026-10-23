# 🏥 Hospital Management System

A comprehensive hospital management system built with FastAPI (Python) backend and React frontend, deployable to AWS with automated CI/CD.

## 🌟 Features

- **Patient Management**: Complete CRUD operations for patient records
- **Department Management**: Organize hospital departments and staff
- **Appointment Scheduling**: Book and manage patient appointments  
- **Inventory Management**: Track medical supplies and equipment
- **Staff Management**: Manage hospital staff and roles
- **AI-Powered Chatbot**: Integrated AI assistance for hospital operations
- **Real-time Updates**: Live data synchronization across the system

## 🏗️ Architecture

- **Backend**: FastAPI with SQLAlchemy ORM
- **Frontend**: React with Vite
- **Database**: PostgreSQL
- **Containerization**: Docker
- **Cloud Platform**: AWS (ECS, RDS, ALB, ECR)
- **CI/CD**: GitHub Actions

## 🚀 Quick Deployment to AWS

### Option 1: Automated Setup (Recommended)
```bash
# Windows
setup-aws.bat

# PowerShell
.\deploy-to-aws.ps1
```

### Option 2: Manual Setup
Follow the complete guide in [`COMPLETE-DEPLOYMENT-GUIDE.md`](docs/deployment/COMPLETE-DEPLOYMENT-GUIDE.md)

## 🛠️ Local Development

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL (optional, can use Docker)

### Quick Start
```bash
# Clone the repository
git clone https://github.com/YOUR-USERNAME/hospital-management-system.git
cd hospital-management-system

# Start with Docker Compose
docker-compose -f docker-compose.simple.yml up -d

# Or start manually:

# Backend
cd backend-python
pip install uv
uv pip install -e .
python comprehensive_server.py

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` for the frontend and `http://localhost:8000` for the API.

## 📦 Project Structure

```
hospital-management-system/
├── backend-python/          # FastAPI + MCP backend
│   ├── hms_agent/           # guarded agent layer (policy, auth, audit, graph)
│   ├── agents/              # domain agents
│   ├── tests/               # unit, security, integration, contract, failure
│   ├── scripts/             # operational scripts
│   ├── database.py          # SQLAlchemy models
│   └── multi_agent_server.py
├── frontend/                # React + Vite
│   └── src/services/        # authenticated API client
├── evals/                   # measurement harnesses
│   ├── datasets/            # labelled cases + generators
│   ├── runners/             # scripts that produce numbers
│   └── results/             # raw output, committed
├── docs/                    # see docs/README.md
│   ├── architecture/        # audit, Phase 20 standard
│   ├── operations/          # cutover, staging gates
│   ├── evaluation/          # measured results
│   ├── deployment/          # AWS, CI/CD, Docker
│   └── guides/              # feature guides
├── deploy/
│   ├── aws/                 # CloudFormation + ECS task definitions
│   └── scripts/             # deployment scripts
├── .github/workflows/       # CI/CD
├── docker-compose.yml
└── nginx.conf
```

Documentation index: [`docs/README.md`](docs/README.md)

## 🔧 API Endpoints

The system provides comprehensive REST API endpoints:

- **Patients**: `/api/patients/` - CRUD operations
- **Departments**: `/api/departments/` - Department management
- **Staff**: `/api/staff/` - Staff management
- **Appointments**: `/api/appointments/` - Appointment scheduling
- **Equipment**: `/api/equipment/` - Equipment tracking
- **Supplies**: `/api/supplies/` - Inventory management
- **Health Check**: `/health` - System health status

## 🌐 AWS Deployment

### Services Used (All Free Tier Eligible)
- **ECS Fargate**: Container orchestration
- **RDS PostgreSQL**: Database (db.t3.micro)
- **Application Load Balancer**: Traffic distribution
- **ECR**: Container registry
- **CloudWatch**: Logging and monitoring
- **VPC**: Network isolation
- **IAM**: Security and permissions

### Estimated Cost: **$0/month** (within free tier limits)

## 🔄 CI/CD Pipeline

Automated deployment with GitHub Actions:
1. **Code Push** → GitHub repository
2. **Build** → Docker images
3. **Test** → Run health checks
4. **Deploy** → Push to ECR → Update ECS services
5. **Monitor** → CloudWatch logs and metrics

## 🔐 Security Features

- Database passwords stored in AWS Systems Manager
- VPC with security groups for network isolation
- Non-root container users
- CORS protection
- Health checks and monitoring
- Automated backups

## 📊 Monitoring

- **CloudWatch Logs**: Application and container logs
- **Health Checks**: Automatic service health monitoring  
- **Metrics**: ECS service and RDS metrics
- **Alerts**: Can be configured for production use

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check [`COMPLETE-DEPLOYMENT-GUIDE.md`](docs/deployment/COMPLETE-DEPLOYMENT-GUIDE.md)
- **Issues**: Create a GitHub issue
- **Logs**: Check CloudWatch logs in AWS Console

## 🎯 Next Steps

After deployment:
- [ ] Set up custom domain with SSL certificate
- [ ] Configure automated backups
- [ ] Set up monitoring alerts
- [ ] Implement user authentication
- [ ] Add comprehensive test suite
- [ ] Set up staging environment

---
