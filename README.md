# Cerebro - Multimodal AI Second Brain

A powerful multimodal AI system that acts as your personal intelligence layer, capable of ingesting, understanding, and reasoning about documents, audio, web content, and images.

## 🧠 Features

- **Multimodal Ingestion**: Process audio (MP3, M4A), documents (PDF, Markdown), web content, and images
- **Temporal-Aware Search**: Smart time-based filtering to answer questions like "What did I work on last month?"
- **Hybrid Retrieval**: Combines semantic search (pgvector) with keyword search for optimal results
- **Streaming Responses**: Real-time, token-by-token AI responses using Server-Sent Events
- **Privacy-First**: Audio files are transcribed and discarded for privacy
- **Perfect Memory**: Grounded responses using only your knowledge base - no hallucinations

## 🏗️ Architecture

### Backend
- **FastAPI**: High-performance async API
- **PostgreSQL + pgvector**: Vector database for semantic search
- **Celery + Redis**: Async task processing
- **Whisper**: Audio transcription
- **OpenAI**: Embeddings and synthesis

### Frontend
- **Next.js**: Modern React framework
- **Tailwind CSS**: Beautiful, responsive UI
- **SSE Streaming**: Real-time chat interface

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key

### 1. Clone and Setup

```bash
cd Cerebro-Multi-modal-AI

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Add your OpenAI API key to backend/.env
# OPENAI_API_KEY=your_api_key_here
```

### 2. Start with Docker

```bash
docker-compose up -d
```

This will start:
- PostgreSQL with pgvector (port 5432)
- Redis (port 6379)
- FastAPI backend (port 8000)
- Celery worker
- Next.js frontend (port 3000)

### 3. Initialize Database

```bash
docker-compose exec backend python -c "from app.core.database import init_db; init_db()"
```

### 4. Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📁 Project Structure

```
Cerebro-Multi-modal-AI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/          # API endpoints
│   │   ├── core/
│   │   │   ├── config.py        # Configuration
│   │   │   └── database.py      # Database setup
│   │   ├── models/
│   │   │   └── document.py      # SQLAlchemy models
│   │   ├── schemas/
│   │   │   └── document.py      # Pydantic schemas
│   │   ├── services/
│   │   │   ├── retrieval_service.py    # Multi-stage retrieval
│   │   │   ├── embedding_service.py    # OpenAI embeddings
│   │   │   ├── synthesis_service.py    # LLM response generation
│   │   │   └── text_chunker.py         # Text chunking
│   │   ├── workers/
│   │   │   ├── audio_worker.py         # Audio transcription
│   │   │   ├── document_worker.py      # Document processing
│   │   │   ├── web_worker.py           # Web scraping
│   │   │   └── image_worker.py         # Image captioning
│   │   └── main.py              # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx             # Main page
│   ├── components/
│   │   ├── ChatInterface.tsx    # Chat UI with SSE
│   │   └── UploadPanel.tsx      # Multi-modal upload
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

## 🔧 Manual Setup (Without Docker)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL with pgvector
createdb cerebro
psql cerebro -c "CREATE EXTENSION vector;"

# Configure .env file
cp .env.example .env
# Edit .env with your settings

# Initialize database
python -c "from app.core.database import init_db; init_db()"

# Start Redis
redis-server

# Start Celery worker (in a separate terminal)
celery -A app.workers.celery_app worker --loglevel=info

# Start FastAPI
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure .env
cp .env.example .env

# Start development server
npm run dev
```

## 🎯 Usage

### 1. Feed Your Brain

Upload content using the right sidebar:

- **Documents**: Drag & drop PDFs or Markdown files
- **Audio**: Upload recordings for transcription
- **Web**: Paste URLs to scrape articles
- **Images**: Upload images for AI captioning

### 2. Query Your Brain

Ask questions in natural language:

- "What did I learn about machine learning last week?"
- "Summarize the main points from the podcast I uploaded"
- "Show me all documents about Python"

### 3. Get Grounded Responses

Cerebro will:
1. Parse temporal intent from your query
2. Search your knowledge base (semantic + keyword)
3. Generate a response based ONLY on retrieved sources
4. Stream the response token-by-token
5. Cite sources used

## ⚙️ Configuration

### Backend Environment Variables

```bash
# OpenAI
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Whisper Model (tiny, base, small, medium, large)
WHISPER_MODEL=base

# Chunking Strategy
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# Privacy
KEEP_AUDIO_FILES=False  # Delete audio after transcription
```

### Retrieval Strategy

The system uses a **4-stage retrieval pipeline**:

1. **Temporal Intent Parsing**: LLM extracts time constraints
2. **Hybrid Search**: Parallel semantic + keyword search
3. **Temporal Filtering**: SQL WHERE clause on dates
4. **Re-ranking**: Cross-encoder scoring (future enhancement)

## 🛠️ Development

### Run Tests

```bash
cd backend
pytest
```

### Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Monitor Celery Tasks

```bash
celery -A app.workers.celery_app flower
```

Access Flower at http://localhost:5555

## 📊 Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| API | FastAPI, Python 3.11 |
| Database | PostgreSQL + pgvector |
| Task Queue | Celery + Redis |
| AI Models | OpenAI (GPT-4, Embeddings), Whisper |
| Frontend | Next.js 14, React, TypeScript |
| Styling | Tailwind CSS |
| Deployment | Docker, Docker Compose |

## 🔒 Security & Privacy

- Audio files are transcribed locally and discarded by default
- All data stored in your own database
- API keys managed via environment variables
- No external data sharing

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check pgvector extension
docker-compose exec postgres psql -U postgres -d cerebro -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

### Celery Worker Not Processing

```bash
# Check Redis connection
redis-cli ping

# Restart worker
docker-compose restart celery_worker

# View worker logs
docker-compose logs -f celery_worker
```

### Frontend Can't Connect to Backend

Check CORS settings in `backend/app/core/config.py`:

```python
ALLOWED_ORIGINS = ["http://localhost:3000"]
```

## 🚀 Production Deployment

For production:

1. Set `DEBUG=False` in backend/.env
2. Use proper PostgreSQL credentials
3. Set up SSL/TLS
4. Use Nginx as reverse proxy
5. Configure proper CORS origins
6. Use production-grade Redis
7. Set up monitoring (e.g., Sentry)




