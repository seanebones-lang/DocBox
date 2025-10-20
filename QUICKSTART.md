# DocBox Quick Start Guide

Get the DocBox Healthcare RAG System running in minutes.

## Prerequisites

Ensure you have the following installed:
- **Docker Desktop** 24+ ([Download](https://www.docker.com/products/docker-desktop))
- **Node.js** 20.x ([Download](https://nodejs.org/))
- **Python** 3.12+ ([Download](https://www.python.org/))
- **Git** ([Download](https://git-scm.com/))

## 1. Clone Repository

```bash
git clone https://github.com/seanebones-lang/DocBox.git
cd DocBox
```

## 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# REQUIRED: Set these critical values
nano .env
```

**Minimum Required Settings:**
```env
# Generate a secure secret key (use: openssl rand -hex 32)
SECRET_KEY=your-generated-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
ENCRYPTION_KEY=generate-using-backend-script
FIELD_ENCRYPTION_KEY=generate-using-backend-script

# Database passwords (change these!)
POSTGRES_PASSWORD=change-me-in-production
NEO4J_PASSWORD=change-me-in-production
REDIS_PASSWORD=change-me-in-production

# LLM API Keys
OPENAI_API_KEY=sk-your-key-here
# OR
ANTHROPIC_API_KEY=sk-your-key-here
```

**Generate Encryption Keys:**
```bash
cd backend
python3 -c "from security.encryption import generate_encryption_key; print(generate_encryption_key())"
cd ..
```

## 3. Start Services

```bash
# Start all services with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

**Services Started:**
- PostgreSQL (port 5432)
- Neo4j (ports 7474, 7687)
- Redis (port 6379)
- Qdrant (ports 6333, 6334)
- FastAPI Backend (port 8000)
- Next.js Web App (port 3000)
- Kiosk App (port 3001)
- Prometheus (port 9090)
- Grafana (port 3100)
- Elasticsearch (port 9200)
- Kibana (port 5601)

## 4. Initialize Databases

```bash
# Make script executable
chmod +x scripts/init-databases.sh

# Run initialization
./scripts/init-databases.sh
```

## 5. Access Applications

| Application | URL | Credentials |
|------------|-----|-------------|
| **API Documentation** | http://localhost:8000/docs | N/A |
| **Admin Web App** | http://localhost:3000 | (Register new account) |
| **Kiosk App** | http://localhost:3001 | N/A |
| **Neo4j Browser** | http://localhost:7474 | neo4j / docbox_neo4j_dev |
| **Grafana** | http://localhost:3100 | admin / admin |
| **Kibana** | http://localhost:5601 | N/A |

## 6. Create First User

**Using API:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@docbox.health",
    "password": "SecurePassword123!",
    "first_name": "Admin",
    "last_name": "User",
    "role": "admin"
  }'
```

**Using Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/auth/register",
    json={
        "email": "admin@docbox.health",
        "password": "SecurePassword123!",
        "first_name": "Admin",
        "last_name": "User",
        "role": "admin"
    }
)
print(response.json())
```

## 7. Test the System

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@docbox.health",
    "password": "SecurePassword123!"
  }'
```

**Get Current User:**
```bash
# Replace YOUR_TOKEN with access_token from login response
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 8. Development Workflow

### Backend Development

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --port 8000
```

### Web App Development

```bash
cd web-app

# Install dependencies
npm install

# Run development server
npm run dev
```

### Kiosk App Development

```bash
cd kiosk-app

# Install dependencies
npm install

# Run development server
npm run dev
```

## 9. Common Tasks

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f postgres
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

### Database Migrations
```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Run Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd web-app
npm test

# E2E tests
npm run test:e2e
```

## 10. Next Steps

1. **Configure Clinics**: Create your first clinic in the admin panel
2. **Add Staff**: Invite doctors, nurses, and receptionists
3. **Set Up Kiosks**: Configure kiosk settings for each location
4. **Index Medical Knowledge**: Upload clinical guidelines to the RAG system
5. **Test Workflows**: Try the appointment scheduling and check-in flows

## Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :8000  # Replace with your port

# Kill process
kill -9 PID
```

### Database Connection Failed
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Restart PostgreSQL
docker-compose restart postgres

# View PostgreSQL logs
docker-compose logs postgres
```

### Cannot Connect to Neo4j
```bash
# Check Neo4j status
docker-compose ps neo4j

# View Neo4j logs
docker-compose logs neo4j

# Restart Neo4j
docker-compose restart neo4j
```

### Module Not Found Errors
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd web-app  # or kiosk-app
npm install
```

### Permission Denied
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Fix file permissions
sudo chown -R $USER:$USER .
```

## Support

- **Documentation**: See README.md and IMPLEMENTATION_STATUS.md
- **Issues**: Open a GitHub issue
- **Security**: Email security@docbox.health
- **General**: support@docbox.health

## Production Deployment

**DO NOT use Docker Compose in production!**

For production deployment, see:
- `kubernetes/` - Kubernetes manifests
- `terraform/` - Infrastructure as Code
- `DEPLOYMENT.md` - Detailed deployment guide

---

**Happy coding! 🚀**

