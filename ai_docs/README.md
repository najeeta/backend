# Thesys C1 Backend Documentation

> **Backend-focused documentation for Thesys C1 implementation in the Anita project**

## Overview

This directory contains backend-specific documentation for implementing Thesys C1 Generative UI features, with a focus on Python/FastAPI implementations, database persistence, and server-side integration patterns.

## Documentation Index

### Available Guides

| Guide | Description | Use Case |
|-------|-------------|----------|
| **[Conversational Persistence](./conversational-persistence.md)** | Store and retrieve chat history with Firebase Firestore | Maintaining conversation state across sessions |

## Quick Reference

### Conversational Persistence

**Key Topics:**
- Firebase Firestore setup (Python & Node.js)
- Thread management (create, list, delete)
- Message storage and retrieval
- Backend API integration
- Security best practices
- Alternative storage options (PostgreSQL, MongoDB, Redis)

**When to Use:**
- Multi-session conversations
- Chat history features
- Thread-based conversations
- User conversation management

## Common Backend Patterns

### 1. Python FastAPI with Firestore

```python
from fastapi import FastAPI, HTTPException
from openai import OpenAI
from firebase_admin import firestore
import os

app = FastAPI()

client = OpenAI(
    base_url='https://api.thesys.dev/v1/embed',
    api_key=os.getenv('THESYS_API_KEY')
)

db = firestore.client()

@app.post("/chat")
async def chat(thread_id: str, message: str):
    # Fetch history
    messages_ref = db.collection('messages')\
                     .where('thread_id', '==', thread_id)\
                     .order_by('created_at')

    history = [
        {'role': msg.to_dict()['role'], 'content': msg.to_dict()['content']}
        for msg in messages_ref.stream()
    ]

    # Add new message
    history.append({'role': 'user', 'content': message})

    # Call C1 API
    response = client.chat.completions.create(
        model='gpt-4',
        messages=history,
        stream=True
    )

    # Stream and save
    full_response = ''
    for chunk in response:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            full_response += content
            yield content

    # Save to Firestore
    db.collection('messages').add({
        'thread_id': thread_id,
        'role': 'assistant',
        'content': full_response,
        'created_at': firestore.SERVER_TIMESTAMP
    })
```

### 2. Environment Configuration

**Required Environment Variables:**

```bash
# .env
THESYS_API_KEY=your_thesys_api_key

# Firebase (Python Backend)
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your_client_id

# Database (if not using Firebase)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
MONGODB_URI=mongodb://localhost:27017/chat
REDIS_URL=redis://localhost:6379
```

### 3. Service Layer Pattern

Organize backend logic into service modules:

```
backend/
├── services/
│   ├── thread_service.py       # Thread management
│   ├── message_service.py      # Message CRUD
│   └── llm_service.py          # C1 API integration
├── api/
│   ├── chat.py                 # Chat endpoints
│   └── threads.py              # Thread endpoints
├── models/
│   ├── thread.py               # Thread models
│   └── message.py              # Message models
└── config/
    ├── firebase.py             # Firebase config
    └── settings.py             # App settings
```

## Integration with Frontend

### API Endpoints

**Typical backend API structure:**

```python
# POST /api/chat
# - Fetch conversation history
# - Call C1 API with context
# - Stream response
# - Save new messages

# GET /api/threads
# - List user's conversation threads

# POST /api/threads
# - Create new conversation thread

# GET /api/threads/:id/messages
# - Get messages for a specific thread

# DELETE /api/threads/:id
# - Delete thread and messages
```

### Request/Response Flow

```
1. Frontend → POST /api/chat
   {
     "thread_id": "abc123",
     "message": "Show me revenue trends",
     "user_id": "user_456"
   }

2. Backend:
   a. Fetch history from database
   b. Build context with historical messages
   c. Call C1 API
   d. Stream response to frontend
   e. Save messages to database

3. Backend → Frontend (Streaming)
   "Here is your revenue chart..."
   [C1 UI components]
```

## Database Schema

### Firebase Firestore

**Collections:**

```
threads/
  {thread_id}/
    - title: string
    - user_id: string
    - created_at: timestamp
    - updated_at: timestamp
    - metadata: object

messages/
  {message_id}/
    - thread_id: string
    - role: string (user|assistant|system)
    - content: string
    - created_at: timestamp
    - metadata: object
```

### PostgreSQL (with Prisma)

```prisma
model Thread {
  id        String   @id @default(cuid())
  title     String
  userId    String
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  messages  Message[]
  metadata  Json?

  @@index([userId])
}

model Message {
  id        String   @id @default(cuid())
  threadId  String
  thread    Thread   @relation(fields: [threadId], references: [id], onDelete: Cascade)
  role      String
  content   String   @db.Text
  createdAt DateTime @default(now())
  metadata  Json?

  @@index([threadId])
  @@index([createdAt])
}
```

## Best Practices

### 1. Error Handling

```python
from fastapi import HTTPException

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Fetch history
        messages = get_messages(request.thread_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch messages: {str(e)}"
        )

    try:
        # Call LLM
        response = client.chat.completions.create(...)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"LLM API error: {str(e)}"
        )

    # Continue...
```

### 2. Authentication

```python
from fastapi import Depends, HTTPException, Header

async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization")

    # Verify token (Firebase Auth, JWT, etc.)
    token = authorization.replace("Bearer ", "")
    user = verify_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user

@app.post("/chat")
async def chat(
    request: ChatRequest,
    user = Depends(get_current_user)
):
    # Ensure user owns the thread
    thread = get_thread(request.thread_id)
    if thread.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Continue...
```

### 3. Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/chat")
@limiter.limit("10/minute")
async def chat(request: Request, chat_req: ChatRequest):
    # Handle chat
    pass
```

### 4. Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/chat")
async def chat(request: ChatRequest):
    logger.info(f"Chat request for thread {request.thread_id}")

    try:
        response = await process_chat(request)
        logger.info(f"Chat completed for thread {request.thread_id}")
        return response
    except Exception as e:
        logger.error(f"Chat failed: {str(e)}", exc_info=True)
        raise
```

### 5. Caching

```python
from functools import lru_cache
import redis

redis_client = redis.from_url(os.getenv('REDIS_URL'))

def get_cached_thread(thread_id: str):
    cached = redis_client.get(f"thread:{thread_id}")
    if cached:
        return json.loads(cached)

    thread = fetch_thread_from_db(thread_id)
    redis_client.setex(
        f"thread:{thread_id}",
        3600,  # 1 hour
        json.dumps(thread)
    )
    return thread
```

## Testing

### Unit Tests

```python
# tests/test_thread_service.py
import pytest
from backend.services.thread_service import create_thread, get_messages

@pytest.fixture
def mock_db(mocker):
    return mocker.patch('backend.services.thread_service.db')

def test_create_thread(mock_db):
    thread = create_thread(user_id="user_123", title="Test Thread")
    assert thread.user_id == "user_123"
    assert thread.title == "Test Thread"
    mock_db.collection.assert_called_with('threads')

def test_get_messages(mock_db):
    messages = get_messages(thread_id="thread_123")
    assert isinstance(messages, list)
```

### Integration Tests

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_chat_endpoint():
    response = client.post("/api/chat", json={
        "thread_id": "test_thread",
        "message": "Hello",
        "user_id": "test_user"
    })
    assert response.status_code == 200

def test_create_thread():
    response = client.post("/api/threads", json={
        "user_id": "test_user",
        "title": "New Thread"
    })
    assert response.status_code == 201
    assert "id" in response.json()
```

## Deployment

### Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export THESYS_API_KEY=your_key
export FIREBASE_PROJECT_ID=your_project

# Run server
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - THESYS_API_KEY=${THESYS_API_KEY}
      - FIREBASE_PROJECT_ID=${FIREBASE_PROJECT_ID}
    volumes:
      - ./backend:/app/backend
```

## Monitoring

### Health Check

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": check_database_connection(),
            "llm_api": check_llm_api(),
        }
    }
```

### Metrics

```python
from prometheus_client import Counter, Histogram
import time

chat_requests = Counter('chat_requests_total', 'Total chat requests')
chat_duration = Histogram('chat_duration_seconds', 'Chat request duration')

@app.post("/chat")
async def chat(request: ChatRequest):
    chat_requests.inc()

    start_time = time.time()
    try:
        response = await process_chat(request)
        return response
    finally:
        chat_duration.observe(time.time() - start_time)
```

## Resources

### Official Documentation
- **Thesys C1 Docs**: [https://docs.thesys.dev](https://docs.thesys.dev)
- **Firebase Admin SDK (Python)**: [https://firebase.google.com/docs/admin/setup](https://firebase.google.com/docs/admin/setup)
- **FastAPI**: [https://fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- **OpenAI Python SDK**: [https://github.com/openai/openai-python](https://github.com/openai/openai-python)

### Related Frontend Docs
- Frontend C1 documentation: `/Users/najik/development/anita/ui/ai_docs/`

## Contributing

When adding new backend documentation:

1. Focus on Python/FastAPI implementations
2. Include complete code examples
3. Document database schemas
4. Add error handling patterns
5. Include security considerations
6. Update this README with links

## Changelog

| Date | Changes |
|------|---------|
| 2025-10-05 | Initial backend documentation created |
| 2025-10-05 | Added Conversational Persistence guide |
