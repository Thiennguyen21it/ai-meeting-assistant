# AI Meeting Assistant - DACN3 Project

An intelligent meeting assistant system that enhances meeting productivity through AI-powered features including real-time transcription, automatic summarization, and action item detection.

## 🚀 Features

### Core Meeting Features

- **Create & Join Meetings**: Easy meeting creation and participation system
- **Real-time Transcription**: Live speech-to-text conversion during meetings
- **Meeting Summarization**: AI-powered automatic meeting summaries
- **Action Items Detection**: Intelligent identification of tasks and action items
- **Content Search**: Search through meeting transcriptions and content
- **Settings & Role Management**: User permissions and meeting configuration

### AI Capabilities

- **Speech Recognition**: Advanced audio processing and transcription
- **Natural Language Processing**: Content analysis and summarization
- **Task Extraction**: Automatic detection of actionable items
- **Smart Search**: Semantic search through meeting content

## 🛠 Tech Stack

### Frontend

- **Next.js** - React framework for modern web applications
- **React** - Component-based UI library
- **TypeScript** - Type-safe JavaScript

### Backend

- **FastAPI** - High-performance Python web framework
- **Python** - Core backend language
- **WebSocket** - Real-time communication

### Database

- **PostgreSQL** - Robust relational database
- **SQLAlchemy** - Database ORM

### AI Services

- **OpenAI API** - GPT models for summarization and NLP
- **Speech-to-Text** - Real-time transcription services

## 📊 Database Schema

### Core Tables

- **Users**: User management and authentication
- **Meetings**: Meeting metadata and configuration
- **Transcriptions**: Real-time speech-to-text data
- **Action_Items**: Extracted tasks and action items

## 🏗 System Architecture

```
Frontend (Next.js) ↔ Backend API (FastAPI) ↔ Database (PostgreSQL)
                           ↓
                    AI Services (OpenAI)
```

## 📦 Installation

### Prerequisites

- Node.js 18+
- Python 3.8+
- PostgreSQL 12+
- OpenAI API key

### Clone Repository

```bash
git clone <repository-url> && cd project_dacn3
```

### Backend Setup

```bash
cd backend

# Install uv for Python package management
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies using uv
uv sync

# Set up environment variables
cp .env.example .env

# Activate virtual environment
source .venv/bin/activate

# Run database migrations
alembic upgrade head

# Start the development server with Docker (recommended)
docker compose -f docker-compose-dev.yml watch

# OR start without Docker
fastapi dev app/main.py
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.local.example .env.local
# Edit .env.local with API endpoints

# Start the development server
npm run dev
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)

```env
DATABASE_URL=postgresql://username:password@localhost:5432/meeting_db
OPENAI_API_KEY=your_openai_api_key
SECRET_KEY=your_secret_key
CORS_ORIGINS=http://localhost:3000
```

#### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## 🚀 Usage

### Starting a Meeting

1. Navigate to the dashboard
2. Click "Create Meeting"
3. Configure meeting settings
4. Share meeting link with participants

### During a Meeting

- **Real-time Transcription**: Speech is automatically transcribed
- **Live Updates**: See transcriptions update in real-time
- **Action Items**: Important tasks are highlighted automatically

### After a Meeting

- **View Summary**: AI-generated meeting summary
- **Action Items**: List of extracted tasks and assignments
- **Search Content**: Find specific topics or discussions
- **Export Data**: Download transcriptions and summaries

## 🔍 API Endpoints

### Authentication

- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `POST /auth/logout` - User logout

### Meetings

- `GET /meetings` - List user meetings
- `POST /meetings` - Create new meeting
- `GET /meetings/{id}` - Get meeting details
- `PUT /meetings/{id}` - Update meeting
- `DELETE /meetings/{id}` - Delete meeting

### Transcriptions

- `GET /meetings/{id}/transcriptions` - Get meeting transcriptions
- `POST /meetings/{id}/transcriptions` - Add transcription
- `WebSocket /ws/meetings/{id}` - Real-time transcription

### AI Features

- `POST /meetings/{id}/summarize` - Generate meeting summary
- `POST /meetings/{id}/action-items` - Extract action items
- `GET /meetings/{id}/search` - Search meeting content

## 🎨 User Interface

### Main Pages

1. **Login/Registration**: User authentication
2. **Dashboard**: Main meeting management interface
3. **Meeting Room**: Live meeting interface with transcription
4. **Meeting Content**: Post-meeting summary and analysis
5. **Schedule View**: Calendar and meeting timeline

## 🔒 Security Features

- JWT-based authentication
- Role-based access control
- Secure WebSocket connections
- Data encryption for sensitive information

## 📱 Responsive Design

The application is fully responsive and works across:

- Desktop browsers
- Tablet devices
- Mobile phones

## 🧪 Testing

```bash
# Backend tests
pytest

# Frontend tests
npm test

# E2E tests
npm run test:e2e
```

## 📈 Performance

- Real-time transcription with minimal latency
- Optimized database queries
- Efficient WebSocket communication
- Cached AI responses for common queries

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is part of the DACN3 (Đồ án chuyên ngành 3) coursework.

## 👥 Team

**NGUYỄN HOÀN THIỆN** - Project Developer

## 📞 Support

For questions and support, please contact the development team or refer to the project documentation.

---

_This AI Meeting Assistant aims to revolutionize how teams conduct and manage meetings through intelligent automation and real-time insights._
