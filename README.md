<h1 align="center">🎯 Adaptive Exam Preparation & Performance Analyzer</h1>

<p align="center">
  <strong>An intelligent, self-hosted platform that transforms unorganized study materials into personalized, adaptive assessments — powered by OCR, NLP, and machine learning.</strong>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" /></a>
  <a href="https://www.djangoproject.com/"><img src="https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django" /></a>
  <a href="https://www.django-rest-framework.org/"><img src="https://img.shields.io/badge/DRF-3.16-A30000?style=for-the-badge&logo=django&logoColor=white" alt="DRF" /></a>
  <a href="https://react.dev/"><img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React" /></a>
  <a href="https://vite.dev/"><img src="https://img.shields.io/badge/Vite-8-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite" /></a>
</p>

<p align="center">
  <a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/PostgreSQL-15-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" /></a>
  <a href="https://redis.io/"><img src="https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis" /></a>
  <a href="https://min.io/"><img src="https://img.shields.io/badge/MinIO-S3--Compatible-C72E49?style=for-the-badge&logo=minio&logoColor=white" alt="MinIO" /></a>
  <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" /></a>
</p>

<br/>

> **Status:** Actively under development. Core backend APIs including auth, workspaces, file ingestion, document processing, quiz generation, scheduling, and dashboard analytics are fully implemented! Frontend integration is currently in progress.

---

## 📖 Overview

Students often struggle with scattered, unorganized study materials across PDFs, question banks, and handwritten notes. **Adaptive Exam Prep** solves this by providing a single platform where students can:

1. **Upload** any study material — typed PDFs, scanned question banks, or handwritten notes.
2. **Extract** knowledge automatically using OCR (EasyOCR + OpenCV) and NLP pipelines — no third-party AI APIs required.
3. **Assess** themselves with dynamically generated, adaptive quizzes tailored to their proficiency.
4. **Track** performance with deep analytics and an intelligent preparedness score powered by a Gradient Boosting ML model.

The entire ML/extraction pipeline is **self-hosted**, running locally without external API dependencies.

---

## ✨ Features

### ✅ Implemented

| Feature | Description |
|---|---|
| **RESTful API** | Fully stateless API layer powered by Django REST Framework with standardized JSON response envelopes. |
| **JWT Authentication** | Secure token-based auth with Argon2 password hashing, refresh token rotation, and automatic blacklisting. |
| **Smart Workspaces** | Isolated, per-user workspaces for organizing subjects, files, and study materials. |
| **File Ingestion Pipeline** | Upload sessions with SHA-256 duplicate detection, content-type validation, and MinIO (S3-compatible) blob storage. |
| **Question Bank Extraction** | Automated PDF parsing via Camelot — extracts MCQs, maps answer keys, and persists to the database. |
| **Handwritten Notes OCR** | PDF → Image → OpenCV preprocessing → EasyOCR extraction → Regex candidate topics → LLM validation (Ollama/Qwen). |
| **Adaptive Quiz Engine** | Dynamically generated assessments based on extracted knowledge graphs and student proficiency levels. |
| **Study Schedule Generator** | Automated, personalized study plans based on exam dates and topic coverage using Ollama LLM. |
| **ML Preparedness Model** | Gradient Boosting model predicting exam readiness based on quiz performance and study habits. |
| **Dashboard API** | User-facing dashboard endpoint aggregating workspace, weekly performance, and ML predictions. |
| **Wallet & Token System** | Built-in token economy (`UserWallet`, `TokenTransaction`) tracking platform usage with credit/debit ledger. |
| **Global Exception Handling** | Consistent error envelope across all endpoints with typed error codes. |
| **Docker Infrastructure** | One-command setup for PostgreSQL, Redis, MinIO, and pgAdmin via Docker Compose. |

### 🚧 In Progress

- **Frontend Integration** — React UI connected to backend auth, workspaces, scheduling, and quiz flows.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React 19 + Vite 8                       │
│               (Authentication UI, Dashboard)                │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/REST (JWT Bearer)
┌──────────────────────────▼──────────────────────────────────┐
│                 Django REST Framework API                    │
│  ┌──────────┐ ┌───────────┐ ┌───────┐ ┌────────────────┐   │
│  │   Auth   │ │ Workspace │ │ Files │ │   Processing   │   │
│  └──────────┘ └───────────┘ └───────┘ └────────────────┘   │
│  ┌──────────┐ ┌───────────┐ ┌───────┐ ┌────────────────┐   │
│  │  Wallet  │ │ Dashboard │ │  Quiz │ │    Schedule    │   │
│  └──────────┘ └───────────┘ └───────┘ └────────────────┘   │
└──────┬────────────┬────────────┬────────────┬───────────────┘
       │            │            │            │
  ┌────▼───┐   ┌────▼───┐  ┌────▼───┐  ┌─────▼─────┐
  │Postgres│   │ Redis  │  │ MinIO  │  │  Ollama   │
  │  15    │   │   7    │  │  (S3)  │  │(Qwen LLM) │
  └────────┘   └────────┘  └────────┘  └───────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.10+, Django 5.2, Django REST Framework, Simple JWT |
| **Frontend** | React 19, Vite 8, Axios, React Router DOM |
| **Database** | PostgreSQL 15 (Alpine) |
| **Cache / Broker** | Redis 7 (Alpine) |
| **Object Storage** | MinIO (S3-compatible), pre-signed upload URLs |
| **OCR / NLP** | EasyOCR, OpenCV, Camelot, PyMuPDF, Pandas |
| **ML** | scikit-learn (Gradient Boosting), joblib |
| **LLM** | Ollama (local) with Qwen 3 models |
| **Infrastructure** | Docker Compose, Makefile automation |
| **DB Admin** | pgAdmin 4 |

---

## 📂 Project Structure

```text
adaptive-exam-platform/
│
├── backend/                    # Django REST API
│   ├── authentication/         #   JWT auth, custom user model, registration & login
│   ├── common/                 #   Shared utilities, response helpers, base models, exception handler
│   ├── config/                 #   Django settings, WSGI/ASGI entry points
│   ├── dashboard/              #   User dashboard aggregation & analytics API
│   ├── files/                  #   File upload sessions, hashing, MinIO integration
│   ├── processing/             #   OCR/NLP extraction pipelines (question banks + handwritten notes)
│   ├── quiz/                   #   Assessment generation, execution & evaluation engine
│   ├── schedule/               #   Study schedule generation via LLM & heuristics
│   ├── storage/                #   MinIO/S3 provider utilities & pre-signed URL generation
│   ├── wallet/                 #   Token balances & transaction ledger
│   ├── workspace/              #   Per-user workspace isolation & management
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/                   # React + Vite SPA
│   ├── src/
│   │   ├── api/                #   API client utilities
│   │   ├── components/         #   Reusable UI components
│   │   ├── context/            #   React context providers
│   │   ├── hooks/              #   Custom React hooks
│   │   ├── routes/             #   Route definitions
│   │   └── utils/              #   Helper functions
│   ├── package.json
│   └── vite.config.js
│
├── docker-compose.yml          # PostgreSQL, Redis, MinIO, pgAdmin services
├── .env.example                # Environment variable template
└── README.md
```

---

## 🔌 API Endpoints

All endpoints return a standardized JSON envelope:

```json
{
  "success": true,
  "message": "...",
  "data": { }
}
```

### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/auth/register/` | Register a new user account | ✗ |
| `POST` | `/api/auth/login/` | Authenticate and receive JWT tokens | ✗ |

### Dashboard

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/dashboard/stats/` | Get aggregated dashboard metrics | ✓ |
| `GET` | `/api/dashboard/weekly-graph/` | Get weekly performance metrics | ✓ |

### Workspaces

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/workspace/create/` | Create a new workspace | ✓ |
| `PATCH` | `/api/workspace/<uuid>/` | Update workspace title/description | ✓ |
| `DELETE` | `/api/workspace/<uuid>/delete/` | Delete a workspace | ✓ |

### File Management

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/files/upload-request/` | Create an upload session with pre-signed URLs | ✓ |
| `POST` | `/api/files/upload-request/finalize/` | Finalize and verify uploaded files | ✓ |

### Processing

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/processing/<uuid>/process/` | Trigger workspace document processing | ✓ |

### Quiz

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/quiz/create/` | Generate a new quiz for a workspace | ✓ |
| `POST` | `/api/quiz/<uuid>/start/` | Start a quiz attempt | ✓ |
| `GET` | `/api/quiz/attempt/<uuid>/question/<int>/` | Get a specific question | ✓ |
| `POST` | `/api/quiz/attempt/<uuid>/answer/` | Submit an answer | ✓ |
| `POST` | `/api/quiz/attempt/<uuid>/submit/` | Finish the quiz attempt | ✓ |
| `GET` | `/api/quiz/attempt/<uuid>/result/` | Get quiz attempt result | ✓ |
| `GET` | `/api/quiz/attempts/` | List all user quiz attempts | ✓ |

### Schedule

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/schedule/generate/` | Generate a study schedule | ✓ |
| `GET` | `/api/schedule/<uuid>/` | Get details of a specific schedule | ✓ |
| `GET` | `/api/schedule/latest/<uuid>/` | Get the latest study schedule for a workspace | ✓ |

---

## 🚀 Getting Started

### Prerequisites

- **[Docker](https://www.docker.com/)** & Docker Compose
- **Python 3.10+** (for running the Django server locally)
- **Node.js 18+** & npm (for the frontend)

### 1. Clone the Repository

```bash
git clone https://github.com/AryanPatel-18/Adaptive-exam-platform.git
cd Adaptive-exam-platform
```

### 2. Configure Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# PostgreSQL
POSTGRES_DB=adaptive_exam_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_PORT=5433

# Redis
REDIS_PORT=6379

# MinIO (S3-compatible storage)
STORAGE_PROVIDER=minio
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
MINIO_BUCKET=adaptive-exam-files
MINIO_REGION=us-east-1
MINIO_SECURE=False
```

### 3. Start Infrastructure Services

Spin up PostgreSQL, Redis, MinIO, and pgAdmin containers:

```bash
docker compose up -d
```

This starts the following services:

| Service | URL | Purpose |
|---------|-----|---------|
| PostgreSQL | `localhost:5433` | Primary database |
| Redis | `localhost:6379` | Caching & message broker |
| MinIO Console | `localhost:9001` | Object storage dashboard |
| MinIO API | `localhost:9000` | S3-compatible storage API |
| pgAdmin | `localhost:5050` | Database administration UI |

### 4. Setup the Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py makemigrations
python manage.py migrate
```

### 5. Setup the Frontend

```bash
cd frontend
npm install
```

### 6. Run the Development Servers

**Backend** (from `backend/`):

```bash
python manage.py runserver
```

> API available at `http://127.0.0.1:8000/`

**Frontend** (from `frontend/`):

```bash
npm run dev
```

> Frontend available at `http://localhost:5173/`

---

## 🧪 Running Tests

```bash
cd backend
python manage.py test
```

> **Note:** Automated test coverage is currently being expanded. Test scaffold files exist for all apps.

---

## 📁 Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_DB` | ✓ | — | PostgreSQL database name |
| `POSTGRES_USER` | ✓ | — | PostgreSQL username |
| `POSTGRES_PASSWORD` | ✓ | — | PostgreSQL password |
| `POSTGRES_PORT` | ✗ | `5433` | PostgreSQL host port |
| `REDIS_PORT` | ✗ | `6379` | Redis host port |
| `STORAGE_PROVIDER` | ✓ | — | Storage backend (`minio`) |
| `MINIO_ENDPOINT` | ✓ | — | MinIO server URL |
| `MINIO_ACCESS_KEY` | ✓ | — | MinIO access key |
| `MINIO_SECRET_KEY` | ✓ | — | MinIO secret key |
| `MINIO_BUCKET` | ✓ | — | Default storage bucket name |
| `MINIO_REGION` | ✗ | `us-east-1` | MinIO region |
| `MINIO_SECURE` | ✗ | `False` | Use HTTPS for MinIO |

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** this repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

Please make sure to:
- Follow existing code patterns and project conventions
- Write descriptive commit messages
- Update documentation as needed

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/AryanPatel-18">Aryan Patel</a>
</p>
