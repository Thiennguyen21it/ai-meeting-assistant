# AI Meeting Assistant - Backend Architecture

## 🏗️ **Clean Architecture Overview**

This backend follows clean architecture principles with clear separation of concerns for the AI Meeting Assistant system.

## 📁 **Directory Structure**

```
backend/
├── app/
│   ├── api/                    # API layer
│   │   ├── routes/            # Route handlers
│   │   │   ├── login.py       # Authentication (login, register, logout)
│   │   │   ├── users.py       # User management
│   │   │   ├── meetings.py    # Meeting CRUD operations
│   │   │   ├── transcriptions.py  # Real-time transcription + WebSocket
│   │   │   └── ai_features.py # AI summarization & action items
│   │   ├── deps.py           # Dependency injection
│   │   └── main.py           # API router configuration
│   ├── services/              # Business logic layer
│   │   ├── __init__.py       # Service exports
│   │   ├── summarization.py  # AI meeting summarization
│   │   ├── action_items_service.py  # AI action item extraction & search
│   │   └── transcription.py  # Speech-to-text services
│   ├── core/                  # Core configuration
│   │   ├── config.py         # Settings and configuration
│   │   ├── db.py             # Database connection
│   │   └── security.py       # JWT and password handling
│   ├── models.py             # Database models and Pydantic schemas
│   ├── crud.py               # Database operations
│   ├── utils.py              # Utility functions
│   └── main.py               # FastAPI application entry point
├── data/                      # Data storage
├── alembic/                   # Database migrations
├── tests/                     # Test suite
├── docker-compose.yml         # Production Docker setup
├── docker-compose-dev.yml     # Development Docker setup
├── Dockerfile                # Container definition
├── pyproject.toml            # Dependencies and project config
└── README.md                 # Setup instructions
```

## 🎯 **Core Features Implemented**

### **1. Authentication System**

- **Route**: `/auth/*`
- **Features**: JWT-based login, user registration, logout
- **Files**: `routes/login.py`, `routes/users.py`

### **2. Meeting Management**

- **Route**: `/meetings/*`
- **Features**: CRUD operations, meeting status management
- **Files**: `routes/meetings.py`

### **3. Real-time Transcription**

- **Route**: `/meetings/{id}/transcriptions`
- **WebSocket**: `/ws/meetings/{id}`
- **Features**: Live speech-to-text, WebSocket connections
- **Files**: `routes/transcriptions.py`, `services/transcription.py`

### **4. AI-Powered Features**

- **Routes**: `/meetings/{id}/summarize`, `/meetings/{id}/action-items`
- **Features**: AI summarization, action item extraction, semantic search
- **Files**: `routes/ai_features.py`, `services/summarization.py`, `services/action_items_service.py`

## 🗄️ **Database Models**

### **Core Entities**

- **User**: Authentication and user management
- **Meeting**: Meeting metadata and status
- **Recording**: Audio/video recording data
- **Transcript**: Speech-to-text transcriptions
- **Summary**: AI-generated meeting summaries
- **ActionItem**: AI-extracted tasks and action items

### **Relationships**

```
User (1) ──→ (N) Meeting
Meeting (1) ──→ (N) Recording
Meeting (1) ──→ (N) ActionItem
Recording (1) ──→ (N) Transcript
Transcript (1) ──→ (N) Summary
```

## 🧠 **AI Services**

### **OpenAI Integration**

- **Model**: GPT-4 for summarization and action item extraction
- **Features**:
  - Meeting summarization with configurable length
  - Action item extraction with assignee detection
  - Semantic search through meeting content

### **Service Layer**

- **Async Architecture**: All AI services use async/await
- **Error Handling**: Robust error handling and fallbacks
- **Configuration**: Centralized API key management

## 🔧 **Technical Stack**

- **Framework**: FastAPI with async support
- **Database**: PostgreSQL with SQLModel ORM
- **Authentication**: JWT tokens with bcrypt password hashing
- **AI Services**: OpenAI GPT-4 API
- **Real-time**: WebSocket for live transcription
- **Package Management**: UV for modern Python dependency management
- **Containerization**: Docker with multi-stage builds

## 🚀 **API Endpoints**

### **Authentication**

- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `POST /auth/logout` - User logout

### **Meetings**

- `GET /meetings` - List user meetings
- `POST /meetings` - Create new meeting
- `GET /meetings/{id}` - Get meeting details
- `PUT /meetings/{id}` - Update meeting
- `DELETE /meetings/{id}` - Delete meeting

### **Transcriptions**

- `GET /meetings/{id}/transcriptions` - Get meeting transcriptions
- `POST /meetings/{id}/transcriptions` - Add transcription
- `WebSocket /ws/meetings/{id}` - Real-time transcription

### **AI Features**

- `POST /meetings/{id}/summarize` - Generate meeting summary
- `POST /meetings/{id}/action-items` - Extract action items
- `GET /meetings/{id}/search` - Search meeting content

### **System**

- `GET /health` - Health check endpoint

## 🧪 **Development**

### **Running the Application**

```bash
# Development with Docker
docker compose -f docker-compose-dev.yml watch

# Or run directly
source .venv/bin/activate
fastapi dev app/main.py
```

### **Database Migrations**

```bash
# Create migration
alembic revision --autogenerate -m "Migration message"

# Apply migrations
alembic upgrade head
```

## 🔒 **Security Features**

- JWT-based authentication with configurable expiration
- Password hashing using bcrypt
- Role-based access control (user/superuser)
- Input validation using Pydantic models
- SQL injection prevention through SQLModel ORM

## 📊 **Monitoring & Health**

- Health check endpoint for monitoring
- Structured logging for debugging
- Error handling with proper HTTP status codes
- Database connection health monitoring

---

_This architecture supports the core AI Meeting Assistant functionality while maintaining clean, maintainable, and scalable code._
