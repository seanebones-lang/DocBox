# DocBox - Enterprise Healthcare RAG System

**Advanced Healthcare Management Platform with AI-Powered RAG, Graph Database, and Self-Check-In Kiosks**

[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-20.x-green.svg)](https://nodejs.org/)
[![HIPAA](https://img.shields.io/badge/HIPAA-compliant-green.svg)]()
[![FHIR](https://img.shields.io/badge/FHIR-R5-orange.svg)](https://hl7.org/fhir/)

---

## ⚠️ PROPRIETARY SOFTWARE

**Copyright © 2025 Sean McDonnell. All Rights Reserved.**

This is proprietary software. Unauthorized use, reproduction, or distribution is strictly prohibited.

**To evaluate or purchase this software:**  
🔗 **[Schedule a meeting at www.bizbot.store](https://www.bizbot.store)**

See [COPYRIGHT.md](COPYRIGHT.md) for full legal terms.

---

## Overview

DocBox is a comprehensive, enterprise-grade healthcare management system designed for small to medium-sized healthcare chains (up to 10 clinic locations). Built with cutting-edge October 2025 technologies, it combines AI-powered Retrieval-Augmented Generation (RAG), graph database relationships, blockchain audit trails, and self-service kiosks to deliver secure, efficient, and patient-centered care.

## Key Features

### AI-Powered Intelligence
- **Agentic RAG System**: LangGraph-powered workflows with iterative reasoning and self-correction
- **Medical Knowledge Base**: Vectorized clinical guidelines, protocols, and drug interaction databases
- **Predictive Analytics**: Early disease detection, no-show prediction, and resource optimization
- **Natural Language Queries**: Chat-based patient record search and clinical decision support
- **Hallucination Prevention**: Multi-layered safety checks with medical fact verification

### Patient Management
- **Multi-Clinic Coordination**: Seamless patient care across up to 10 locations
- **Graph-Based Relationships**: Track patient journeys, referrals, and care teams
- **Self-Check-In Kiosks**: Biometric authentication, intake forms, payment processing
- **Remote Monitoring**: 5G-enabled IoT integration with wearable devices
- **Personalized Medicine**: Optional genomic data integration for precision care

### Security & Compliance
- **HIPAA Compliant**: AES-256 encryption, TLS 1.3, comprehensive audit logging
- **GDPR Ready**: Data portability, right to erasure, consent management
- **Zero Trust Architecture**: Continuous authentication with AI-powered threat detection
- **Blockchain Audit Trails**: Immutable records using Hyperledger Fabric
- **FHIR R5 Compliant**: Seamless interoperability with external EHR systems

### Modern Technology Stack (October 2025)
- **Backend**: Python 3.12 + FastAPI 0.115+ with async/await
- **Frontend**: Next.js 15 + React 19 with Server Components
- **RAG Engine**: LangChain 0.3+ with LangGraph for agentic workflows
- **Databases**: PostgreSQL 17 (pgvector 0.7+), Neo4j 5.x, Redis 7.x
- **Vector DB**: Qdrant with hybrid search (dense + sparse embeddings)
- **LLM**: OpenAI GPT-4 Turbo / Claude 3.5 Sonnet
- **Auth**: Auth0/AWS Cognito with WebAuthn passkey support
- **Deployment**: Docker + Kubernetes on AWS/GCP

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Patient Interfaces                        │
├──────────────────┬──────────────────┬──────────────────────────┤
│   Kiosk PWA      │   Patient Portal │   Staff Web App          │
│   (Biometric)    │   (Mobile/Web)   │   (Admin Dashboard)      │
└────────┬─────────┴─────────┬────────┴──────────┬───────────────┘
         │                   │                   │
         └───────────────────┴───────────────────┘
                             │
                    ┌────────▼─────────┐
                    │   API Gateway    │
                    │  (FastAPI + Auth)│
                    └────────┬─────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐      ┌──────▼──────┐     ┌─────▼─────┐
    │  RAG    │      │   Graph DB  │     │ Blockchain│
    │ Engine  │      │   (Neo4j)   │     │  Ledger   │
    │(LangG.) │      │             │     │ (Hyperl.) │
    └────┬────┘      └──────┬──────┘     └─────┬─────┘
         │                  │                   │
    ┌────▼────────────┬─────▼──────┬───────────▼──────┐
    │  Vector DB      │ PostgreSQL │    Redis Cache   │
    │  (Qdrant)       │  (Primary) │   (Sessions)     │
    └─────────────────┴────────────┴──────────────────┘
         │
    ┌────▼─────────────────────────────────────────────┐
    │  External Integrations                            │
    ├──────────────┬──────────────┬────────────────────┤
    │ IoT Devices  │ FHIR APIs    │ Payment Gateways   │
    │ (Wearables)  │ (EHR Sync)   │ (PCI-DSS)         │
    └──────────────┴──────────────┴────────────────────┘
```

## Quick Start

### Prerequisites

```bash
# Required software
- Docker 24+ and Docker Compose
- Node.js 20.x
- Python 3.12+
- PostgreSQL 17
- Neo4j 5.x
- Redis 7.x
```

### Installation

```bash
# Clone repository
git clone https://github.com/seanebones-lang/DocBox.git
cd DocBox

# Copy environment configuration
cp .env.example .env

# Configure your API keys and database credentials
nano .env

# Start all services with Docker Compose
docker-compose up -d

# Initialize databases
./scripts/init-databases.sh

# Run database migrations
cd backend && alembic upgrade head

# Seed initial data
python scripts/seed_data.py
```

### Development Setup

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Web app setup
cd web-app
npm install
npm run dev

# Kiosk app setup
cd kiosk-app
npm install
npm run dev
```

### Access Points

- **API Documentation**: http://localhost:8000/docs
- **Admin Dashboard**: http://localhost:3000
- **Kiosk Interface**: http://localhost:3001
- **Neo4j Browser**: http://localhost:7474
- **Monitoring (Grafana)**: http://localhost:3100

## Project Structure

```
DocBox/
├── backend/                      # FastAPI backend
│   ├── api/                      # API routes
│   │   ├── routes/
│   │   │   ├── auth.py          # Authentication & MFA
│   │   │   ├── patients.py      # Patient management
│   │   │   ├── appointments.py  # Scheduling
│   │   │   ├── clinics.py       # Multi-location mgmt
│   │   │   ├── kiosk.py         # Kiosk endpoints
│   │   │   ├── rag.py           # RAG queries
│   │   │   └── graph.py         # Graph analytics
│   │   └── middleware/          # Security middleware
│   ├── models/                   # Database models
│   │   ├── patient.py
│   │   ├── appointment.py
│   │   ├── clinic.py
│   │   └── user.py
│   ├── database/                 # DB connections
│   │   ├── postgres.py
│   │   └── migrations/
│   ├── graph/                    # Neo4j integration
│   │   ├── neo4j_client.py
│   │   └── schemas.py
│   ├── rag/                      # RAG system
│   │   ├── retrieval.py         # Hybrid search
│   │   ├── embeddings.py        # Vector generation
│   │   ├── agents.py            # LangGraph agents
│   │   └── reranker.py          # Result reranking
│   ├── security/                 # Security layer
│   │   ├── encryption.py        # PHI encryption
│   │   ├── audit.py             # Audit logging
│   │   ├── auth.py              # JWT/OAuth
│   │   └── blockchain.py        # Hyperledger client
│   ├── compliance/               # HIPAA/GDPR
│   │   ├── hipaa.py
│   │   └── gdpr.py
│   ├── iot/                      # IoT integration
│   │   ├── wearables.py
│   │   └── monitoring.py
│   ├── fhir/                     # FHIR R5 API
│   │   ├── resources.py
│   │   └── transformers.py
│   ├── tests/                    # Test suite
│   └── main.py                   # App entry point
├── web-app/                      # Admin dashboard (Next.js 15)
│   ├── app/
│   │   ├── dashboard/
│   │   ├── patients/
│   │   ├── appointments/
│   │   ├── analytics/
│   │   └── settings/
│   ├── components/
│   │   ├── PatientSearch.tsx    # RAG-powered search
│   │   ├── AppointmentCalendar.tsx
│   │   └── AnalyticsDashboard.tsx
│   ├── lib/
│   │   ├── api-client.ts
│   │   └── auth.ts
│   └── tests/
├── kiosk-app/                    # Self-check-in kiosk (Next.js 15 PWA)
│   ├── app/
│   │   ├── page.tsx             # Welcome screen
│   │   ├── verify/              # Patient verification
│   │   ├── checkin/             # Check-in flow
│   │   ├── forms/               # Intake forms
│   │   └── payment/             # Payment processing
│   ├── components/
│   │   ├── BiometricAuth.tsx    # Facial/fingerprint
│   │   ├── InsuranceScanner.tsx # OCR scanning
│   │   └── PaymentTerminal.tsx
│   └── lib/
│       └── offline-sync.ts      # Offline capabilities
├── blockchain/                   # Hyperledger Fabric
│   ├── chaincode/
│   └── network-config/
├── kubernetes/                   # K8s deployment
│   ├── deployments/
│   ├── services/
│   ├── ingress/
│   └── helm/
├── terraform/                    # Infrastructure as Code
│   ├── aws/
│   └── gcp/
├── docs/                         # Documentation
│   ├── architecture/
│   ├── api/
│   ├── deployment/
│   └── compliance/
├── scripts/                      # Utility scripts
│   ├── init-databases.sh
│   ├── seed_data.py
│   └── backup.sh
├── docker-compose.yml            # Local development
├── .env.example                  # Environment template
└── README.md                     # This file
```

## Core Features

### 1. Agentic RAG System

The system uses LangGraph to create intelligent agents that can:
- Decompose complex medical queries into sub-questions
- Iteratively retrieve and verify information
- Cross-reference patient data with medical literature
- Provide citations with confidence scores
- Detect and prevent hallucinations

**Example Query:**
```python
query = "What are the contraindications for prescribing metformin to patient #12345?"
response = await rag_agent.query(
    question=query,
    patient_id="12345",
    include_citations=True
)
```

Reference: [Advanced RAG Systems 2025](https://medium.com/@martinagrafsvw25/advancements-in-rag-retrieval-augmented-generation-systems-by-mid-2025-935a39c15ae9)

### 2. Graph Database Relationships

Neo4j models complex healthcare relationships:
- Patient → Doctor (TREATED_BY)
- Patient → Appointment (ATTENDED)
- Doctor → Clinic (WORKS_AT)
- Patient → Diagnosis (DIAGNOSED_WITH)
- Patient → Medication (PRESCRIBED)
- Patient → Family Member (RELATED_TO)

**Example Cypher Query:**
```cypher
MATCH (p:Patient {id: '12345'})-[:TREATED_BY]->(d:Doctor)-[:WORKS_AT]->(c:Clinic)
RETURN p, d, c
```

### 3. Self-Check-In Kiosk

Features:
- **Biometric Authentication**: Face recognition with liveness detection
- **Document Scanning**: OCR for insurance cards and IDs
- **Digital Forms**: HIPAA-compliant e-signatures
- **Payment Processing**: PCI-DSS compliant card terminals
- **Offline Mode**: Sync when connection restored
- **Accessibility**: WCAG 2.2 Level AA compliant

Reference: [Healthcare Technology Trends 2025](https://www.rxnt.com/8-emerging-trends-in-healthcare-technology-for-2025/)

### 4. Blockchain Audit Trail

Hyperledger Fabric provides:
- Immutable access logs for all PHI access
- Patient consent tracking
- Inter-clinic data sharing verification
- Smart contracts for automated BAAs
- Cryptographic proof of data integrity

Reference: [Healthcare Blockchain 2025](https://healthindustrytrends.com/emerging-healthcare-technologies-for-2025/)

### 5. IoT & Remote Monitoring

Integration with wearable devices:
- Apple Watch, Fitbit, Oura Ring
- Real-time vital signs (heart rate, SpO2, temperature)
- Predictive alerts for abnormal patterns
- Hospital-at-home program support
- Edge computing for low-latency processing

Reference: [5G Healthcare 2025](https://www.techaheadcorp.com/blog/2025-health-it-trends-emerging-technologies-ai-remains-prominent/)

### 6. FHIR R5 Compliance

Full interoperability with external systems:
- Patient resources (FHIR Patient, Observation, Condition)
- Appointment scheduling (FHIR Appointment, Schedule)
- Medication management (FHIR MedicationRequest)
- Document exchange (FHIR DocumentReference)
- Real-time notifications (FHIR Subscription)

## Security Features

### Encryption
- **At Rest**: AES-256 encryption for all PHI in PostgreSQL
- **In Transit**: TLS 1.3 for all API communications
- **Field-Level**: Additional encryption for sensitive fields (SSN, genomic data)

### Authentication & Authorization
- **JWT Tokens**: 15-minute access tokens, 7-day refresh tokens
- **MFA**: Time-based OTP and WebAuthn passkeys
- **RBAC**: Role-based access control (Patient, Doctor, Nurse, Admin, Kiosk)
- **Zero Trust**: Continuous verification of all access requests

### Audit Logging
- **Who**: User ID and role
- **What**: Action performed (read, write, delete)
- **When**: Timestamp with timezone
- **Where**: IP address and location
- **Why**: Reason for access (when applicable)
- **Retention**: 7 years (HIPAA requirement)

### Vulnerability Management
- **OWASP Top 10**: Protection against common web vulnerabilities
- **Dependency Scanning**: Automated checks with Snyk
- **Penetration Testing**: Regular third-party security audits
- **Bug Bounty**: Responsible disclosure program

## API Documentation

Full API documentation available at `/docs` (Swagger UI) and `/redoc` (ReDoc).

### Key Endpoints

#### Authentication
```
POST   /api/v1/auth/login              # User login
POST   /api/v1/auth/mfa/verify         # MFA verification
POST   /api/v1/auth/refresh            # Refresh access token
POST   /api/v1/auth/logout             # Logout
```

#### Patients
```
GET    /api/v1/patients                # List patients
POST   /api/v1/patients                # Create patient
GET    /api/v1/patients/{id}           # Get patient details
PUT    /api/v1/patients/{id}           # Update patient
DELETE /api/v1/patients/{id}           # Delete patient (soft delete)
GET    /api/v1/patients/{id}/history   # Medical history
```

#### Appointments
```
GET    /api/v1/appointments            # List appointments
POST   /api/v1/appointments            # Schedule appointment
PUT    /api/v1/appointments/{id}       # Update appointment
DELETE /api/v1/appointments/{id}       # Cancel appointment
GET    /api/v1/appointments/availability # Check availability
```

#### RAG Queries
```
POST   /api/v1/rag/query               # Natural language query
POST   /api/v1/rag/search              # Semantic search
GET    /api/v1/rag/citations/{id}      # Get source citations
```

#### Graph Insights
```
GET    /api/v1/graph/patient/{id}/network    # Patient care network
GET    /api/v1/graph/referrals                # Referral patterns
GET    /api/v1/graph/care-pathways            # Care pathway analysis
```

#### Kiosk
```
POST   /api/v1/kiosk/verify            # Verify patient identity
POST   /api/v1/kiosk/checkin           # Check-in for appointment
POST   /api/v1/kiosk/forms/submit      # Submit intake forms
POST   /api/v1/kiosk/payment           # Process payment
```

## Deployment

### Local Development
```bash
docker-compose up -d
```

### Production (Kubernetes)
```bash
# Build and push images
./scripts/build-images.sh

# Deploy to Kubernetes
kubectl apply -f kubernetes/

# Or use Helm
helm install docbox ./kubernetes/helm/docbox
```

### Infrastructure as Code (Terraform)
```bash
cd terraform/aws  # or terraform/gcp
terraform init
terraform plan
terraform apply
```

## Testing

### Run All Tests
```bash
# Backend tests
cd backend
pytest --cov=. --cov-report=html

# Frontend tests
cd web-app
npm test

# E2E tests
npm run test:e2e

# Load testing
k6 run tests/load/api-load-test.js
```

### Security Testing
```bash
# OWASP ZAP scan
./scripts/security-scan.sh

# Dependency vulnerabilities
snyk test

# HIPAA compliance check
./scripts/hipaa-audit.sh
```

## Monitoring & Observability

### Metrics (Prometheus)
- API response times
- Database query performance
- RAG query latency
- Kiosk transaction success rate
- Error rates and types

### Logs (ELK Stack)
- Structured JSON logging
- Centralized log aggregation
- Full-text search capabilities
- 7-year retention for audit logs

### Tracing (OpenTelemetry)
- Distributed tracing across microservices
- RAG pipeline visualization
- Database query tracing
- External API call tracking

### Alerting (PagerDuty)
- Critical system failures
- Security incidents
- HIPAA compliance violations
- Performance degradation

## Compliance

### HIPAA Compliance Checklist
- [x] Access controls and authentication
- [x] Encryption at rest and in transit
- [x] Audit logging (7-year retention)
- [x] Automatic session timeout
- [x] Business Associate Agreements tracking
- [x] Breach notification system
- [x] Regular security assessments
- [x] Employee training materials

### GDPR Compliance
- [x] Right to access (data export)
- [x] Right to erasure (data deletion)
- [x] Data portability (FHIR format)
- [x] Consent management
- [x] Data processing agreements
- [x] Privacy by design

## Performance Benchmarks

- **API Response Time**: < 100ms (p95)
- **RAG Query Latency**: < 2s (p95)
- **Database Queries**: < 50ms (p95)
- **Kiosk Check-In Time**: < 60s (average)
- **Concurrent Users**: 1000+ supported
- **Uptime SLA**: 99.9%

## Contributing

This is a proprietary healthcare system. Internal contributors should follow:

1. Read `CONTRIBUTING.md`
2. Create feature branch from `develop`
3. Write tests (minimum 80% coverage)
4. Pass security scans
5. Submit pull request with detailed description
6. Obtain approval from 2+ reviewers
7. Merge to `develop` (staging deployment)
8. Production release via `main` branch

## ⚠️ PROPRIETARY SOFTWARE - LICENSE REQUIRED FOR EVALUATION

**IMPORTANT LEGAL NOTICE: This is COMMERCIAL SOFTWARE FOR SALE**

### 🚫 NOT OPEN SOURCE - NOT FREE SOFTWARE

This software is **NOT**:
- Open source software
- Free software  
- Available under any permissive license
- Free to use, modify, or distribute

### 💼 COMMERCIAL SOFTWARE FOR SALE

**Copyright © 2025 Sean McDonnell. All Rights Reserved.**

This is a **COMMERCIAL SOFTWARE PRODUCT** that is:
- ✅ **FOR SALE** - Available for purchase
- ✅ **LICENSABLE** - Commercial licensing available  
- ✅ **PROPRIETARY** - All rights reserved

### 📋 EVALUATION LICENSE REQUIRED

**To evaluate this software, you MUST:**
1. Contact Sean McDonnell for proper licensing
2. Obtain written evaluation permission
3. Agree to evaluation terms and conditions

**Unauthorized evaluation is strictly prohibited.**

### 🔒 VIEWING ≠ LICENSE TO USE

**Important:** Access to this repository or viewing the source code does **NOT** grant any rights to:
- Use the software
- Modify the software
- Distribute the software
- Create derivative works
- Evaluate or test the software

### 📞 LICENSING CONTACT

**For all licensing inquiries:**
- **Website**: [www.bizbot.store](https://www.bizbot.store)
- **Purpose**: Evaluation licensing, commercial licensing, purchase inquiries
- **Owner**: Sean McDonnell

### ⚖️ LEGAL ENFORCEMENT

Unauthorized use may result in:
- Civil litigation
- Criminal prosecution
- Monetary damages
- Injunctive relief
- Recovery of legal fees

### 📄 FULL LICENSE TERMS

- See [LICENSE](LICENSE) for complete legal terms
- See [COPYRIGHT.md](COPYRIGHT.md) for full copyright notice
- See [NOTICE.md](NOTICE.md) for legal notice
- All intellectual property rights reserved
- No implied licenses granted

## Contact & Support

### Business Inquiries

**To evaluate, purchase, or license DocBox:**

🔗 **[www.bizbot.store](https://www.bizbot.store)**

**Owner**: Sean McDonnell  
**Product**: DocBox Healthcare RAG System

### Support Channels

- **Business Inquiries**: Schedule via [www.bizbot.store](https://www.bizbot.store)
- **Licensing Questions**: Contact through [www.bizbot.store](https://www.bizbot.store)
- **Technical Demos**: Available by appointment at [www.bizbot.store](https://www.bizbot.store)

### Copyright Notice

© 2025 Sean McDonnell. All Rights Reserved.  
See [COPYRIGHT.md](COPYRIGHT.md) for full legal terms.

## Roadmap

### Q1 2026
- [ ] Multi-language support (50+ languages)
- [ ] Voice-based patient interaction
- [ ] AR surgical guidance integration
- [ ] Advanced genomics pipeline

### Q2 2026
- [ ] Federated learning for privacy-preserving AI
- [ ] Quantum-resistant encryption
- [ ] Expanded IoT device support
- [ ] Mobile app (iOS/Android)

### Q3 2026
- [ ] AI-powered clinical decision support
- [ ] Automated prior authorization
- [ ] Social determinants of health tracking
- [ ] International expansion (EU, APAC)

---

**Built with cutting-edge October 2025 technology stack for the future of healthcare.**

