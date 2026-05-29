# Breathe ESG — Operations Platform

A production-ready ESG (Environmental, Social, Governance) data ingestion and review platform. Processes SAP fuel exports, utility electricity invoices, and corporate travel data through a normalization and validation pipeline, with a full audit trail and analyst review workflow.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Django 5 + Django REST Framework |
| **Database** | PostgreSQL (Neon serverless) |
| **Frontend** | React 18 + Vite + TypeScript |
| **State** | TanStack React Query |
| **Styling** | Tailwind CSS |

---

## Project Structure

```
breathe_esg/
├── breathe_esg_django/     # Django backend API
│   ├── api/
│   │   ├── models.py           # 6 core models
│   │   ├── serializers.py      # DRF serializers (camelCase)
│   │   ├── views/              # REST endpoints
│   │   ├── services/           # Business logic
│   │   ├── parsers/            # SAP CSV, Utility CSV, Travel JSON
│   │   ├── normalization/      # 3 normalization strategies
│   │   ├── validation/         # 10 validation rules + engine
│   │   └── migrations/         # Django DB migrations
│   ├── breathe_esg/settings/   # base / local / production
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example            # copy to .env and fill in values
│
└── breathe-esg-frontend/   # React frontend
    ├── src/
    │   ├── pages/          # Dashboard, Review, Upload, Audit, Flags
    │   ├── components/     # Reusable UI components
    │   ├── hooks/          # useDebounce, useQueryKeys
    │   ├── services/       # Axios API services
    │   └── types/          # TypeScript interfaces
    └── .env.example        # copy to .env and fill in values
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL database (or a [Neon](https://neon.tech) free tier account)

### 1. Backend Setup

```bash
cd breathe_esg_django

# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL and SECRET_KEY

# Run migrations (creates all tables + seed data)
python manage.py migrate --settings=breathe_esg.settings.local

# Start the development server
python manage.py runserver 8000 --settings=breathe_esg.settings.local
```

API will be available at **http://localhost:8000**  
Swagger docs at **http://localhost:8000/api/schema/swagger-ui/**

### 2. Frontend Setup

```bash
cd breathe-esg-frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit VITE_API_BASE_URL if your backend is not on port 8000

# Start the dev server
npm run dev
```

Frontend will be available at **http://localhost:5173**

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/records` | Paginated, filtered records list |
| GET | `/api/records/summary` | Dashboard counts |
| GET | `/api/records/datasources` | Active data sources |
| GET | `/api/records/<id>` | Single record detail |
| POST | `/api/records/<id>/approve` | Approve a record |
| POST | `/api/records/<id>/reject` | Reject a record |
| PATCH | `/api/records/<id>` | Edit a record |
| POST | `/api/uploads` | Ingest a file |
| GET | `/api/uploads` | Upload history |
| GET | `/api/audits` | Audit log |
| GET | `/api/audits/entity/<id>` | Entity audit trail |
| GET | `/api/flags` | Data quality flags |

---

## Environment Variables

### Backend (`breathe_esg_django/.env`)

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` for dev, `False` for production |
| `DATABASE_URL` | PostgreSQL connection URL |
| `ALLOWED_HOSTS` | Comma-separated hostnames |
| `CORS_ALLOWED_ORIGINS` | Comma-separated allowed frontend origins |

### Frontend (`breathe-esg-frontend/.env`)

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | Backend API URL (e.g., `http://localhost:8000`) |
| `VITE_COMPANY_ID` | Default company UUID for `X-Company-Id` header |
| `VITE_ANALYST_NAME` | Default analyst name for `X-Analyst-Name` header |

---

## Key Design Decisions

- **Immutable audit trail** — `AuditLog` is append-only with before/after JSON snapshots
- **Record state machine** — only `Pending/Flagged → Approved/Rejected` transitions are valid
- **SHA-256 dedup** — re-uploading the same file returns a 409 Conflict
- **DB connection pooling** — `CONN_MAX_AGE=60` keeps Neon connections warm
- **API caching** — summary (30s) and datasources (5min) cached in memory

---

## License

MIT
