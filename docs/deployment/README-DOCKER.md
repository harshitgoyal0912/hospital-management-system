# Hospital Management System - Docker Environment Setup

## 🏥 Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed on your system
- At least 4GB of available RAM
- Ports 3000, 5432, and 8000 available

### 🚀 Start the System

1. **Clone the repository and navigate to it:**
   ```bash
   cd hospital-management-system
   ```

2. **Set up environment variables (optional):**
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys if needed
   ```

3. **Start the services using Docker Compose:**
   ```bash
   # Simple startup (no reverse proxy)
   docker-compose -f docker-compose.simple.yml up --build

   # Or with full setup including Nginx reverse proxy
   docker-compose up --build
   ```

4. **Access the application:**
   - **Frontend:** http://localhost:3000
   - **Backend API:** http://localhost:8000
   - **Database:** localhost:5432 (postgres/postgres)

### 🔧 Available Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | React.js web application |
| Backend | 8000 | Python FastAPI + FastMCP server |
| PostgreSQL | 5432 | Database server |
| Nginx | 80 | Reverse proxy (optional) |

### 📊 Health Checks

Check if services are running:
```bash
# Backend health check
curl http://localhost:8000/health

# List available MCP tools
curl http://localhost:8000/tools/list
```

### 🛠️ Development Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose down && docker-compose up --build

# Access backend container shell
docker exec -it hospital_backend bash

# Access database
docker exec -it hospital_postgres psql -U postgres -d hospital_management
```

### 📁 Data Persistence

- Database data is persisted in Docker volume `postgres_data`
- To reset the database: `docker-compose down -v`

### 🔑 Environment Variables

Set these in your `.env` file for full functionality:

```env
# AI API Keys (optional)
VITE_OPENAI_API_KEY=your_openai_api_key_here
VITE_CLAUDE_API_KEY=your_claude_api_key_here
VITE_GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Database (automatically configured)
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/hospital_management
```

### 🐛 Troubleshooting

1. **Port conflicts:** Ensure ports 3000, 5432, 8000 are not in use
2. **Database connection:** Wait for PostgreSQL to fully start (check logs)
3. **Build issues:** Try `docker system prune` to clean up Docker cache
4. **Permission issues:** Ensure Docker has proper permissions

### 📈 Production Deployment

For production deployment:
1. Use the full `docker-compose.yml` with Nginx
2. Set proper environment variables
3. Configure SSL certificates
4. Set up proper backup strategies
5. Monitor with Docker health checks
