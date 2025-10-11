# ThesisLink - Academic Supervisor Outreach Management Tool

A lightweight web application for graduate students to manage academic supervisor outreach, email personalization, and follow-up tracking.

## Features

### ✅ Implemented (Backend MVP)

- **Supervisor CRM**: Manage professor contacts with full CRUD operations
- **Template Management**: Create and manage email templates with placeholder support
- **AI Personalization**: OpenAI GPT integration for intelligent email personalization
- **Document Management**: Upload and manage CVs, SOPs, and transcripts
- **Batch Email Sending**: Send personalized emails to multiple contacts with delays
- **Follow-Up Scheduling**: Automated follow-up scheduling with Celery
- **Dashboard Analytics**: Track outreach pipeline, activity logs, and statistics
- **JWT Authentication**: Secure user authentication and authorization
- **RESTful API**: Comprehensive API with auto-generated Swagger documentation

### 🚧 To Be Implemented

- **Frontend**: React + TailwindCSS UI
- **Gmail API Integration**: Alternative to SMTP for sending emails
- **Real-time Notifications**: WebSocket support for live updates

## Tech Stack

### Backend
- **Framework**: FastAPI 0.109.0
- **Database**: SQLAlchemy with PostgreSQL/SQLite support
- **Authentication**: JWT with python-jose
- **Task Queue**: Celery with Redis
- **Email**: SMTP (aiosmtplib) with Gmail API support planned
- **AI**: OpenAI GPT-4 for email personalization
- **File Storage**: Local filesystem with validation

### Frontend (Planned)
- React.js with Vite
- TailwindCSS for styling
- Redux or Zustand for state management
- Axios for API calls

## Project Structure

```
ThesisLink/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   │   ├── auth.py       # Authentication endpoints
│   │   │   ├── contacts.py   # Contact management
│   │   │   ├── templates.py  # Template management
│   │   │   ├── documents.py  # File upload/download
│   │   │   ├── email.py      # Email sending
│   │   │   └── dashboard.py  # Analytics & stats
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   │   ├── auth_service.py
│   │   │   ├── email_service.py
│   │   │   ├── llm_service.py
│   │   │   ├── file_service.py
│   │   │   └── scheduler_service.py
│   │   ├── utils/            # Utilities
│   │   ├── config.py         # Configuration
│   │   ├── database.py       # Database setup
│   │   └── main.py           # FastAPI app
│   ├── tests/                # Test files
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                 # To be implemented
├── docker-compose.yml
└── README.md
```

## Installation & Setup

### Prerequisites

- Python 3.11+
- PostgreSQL (or use SQLite for development)
- Redis (for Celery task queue)
- OpenAI API key (for AI personalization)
- Gmail SMTP credentials (for email sending)

### Local Development Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd ThesisLink
```

2. **Set up backend**
```bash
cd backend
python -m venv venv
```

On Windows:
```powershell
.\venv\Scripts\Activate.ps1
```

On Linux/Mac:
```bash
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
SECRET_KEY=your-secure-secret-key
DATABASE_URL=sqlite:///./thesislink.db
OPENAI_API_KEY=your-openai-api-key
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
REDIS_URL=redis://localhost:6379/0
```

5. **Run the application**
```bash
cd backend
uvicorn app.main:app --reload
```

The API will be available at: http://localhost:8000
API Documentation: http://localhost:8000/api/docs

6. **Start Celery worker (in a new terminal)**
```bash
cd backend
celery -A app.services.scheduler_service.celery_app worker --loglevel=info
```

7. **Start Celery beat scheduler (in another terminal)**
```bash
cd backend
celery -A app.services.scheduler_service.celery_app beat --loglevel=info
```

### Docker Setup (Recommended)

1. **Create .env file** in the project root:
```env
SECRET_KEY=your-secure-secret-key
OPENAI_API_KEY=your-openai-api-key
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
DEBUG=True
```

2. **Start all services**
```bash
docker-compose up -d
```

This will start:
- PostgreSQL database (port 5432)
- Redis (port 6379)
- Backend API (port 8000)
- Celery worker
- Celery beat scheduler

3. **View logs**
```bash
docker-compose logs -f backend
```

4. **Stop services**
```bash
docker-compose down
```

## API Documentation

### Authentication

**Register a new user**
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123",
  "full_name": "John Doe"
}
```

**Login**
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=johndoe&password=SecurePass123
```

Returns JWT token:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### Contacts

**Create contact**
```http
POST /api/contacts/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Dr. Jane Smith",
  "email": "jane.smith@university.edu",
  "university": "MIT",
  "department": "Computer Science",
  "research_interest": "Machine Learning, NLP",
  "website": "https://example.com",
  "notes": "Interested in PhD supervision"
}
```

**List contacts**
```http
GET /api/contacts/?page=1&page_size=20&status=new&search=MIT
Authorization: Bearer <token>
```

**Get contact statistics**
```http
GET /api/contacts/stats/summary
Authorization: Bearer <token>
```

### Templates

**Create template**
```http
POST /api/templates/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "PhD Application Template",
  "subject": "PhD Application Inquiry - [ResearchTopic]",
  "body": "Dear Professor [ProfName],\n\nI am writing to express my interest in joining your research group at [University]...",
  "is_default": true,
  "use_ai_personalization": true
}
```

**Personalize template**
```http
POST /api/templates/personalize?use_ai=true
Authorization: Bearer <token>
Content-Type: application/json

{
  "template_id": 1,
  "contact_id": 1,
  "additional_context": "Mention my background in deep learning"
}
```

### Email

**Send single email**
```http
POST /api/email/send
Authorization: Bearer <token>
Content-Type: application/json

{
  "contact_id": 1,
  "template_id": 1,
  "use_ai": true
}
```

**Send batch emails**
```http
POST /api/email/batch
Authorization: Bearer <token>
Content-Type: application/json

{
  "contact_ids": [1, 2, 3],
  "template_id": 1,
  "use_ai": false,
  "delay_seconds": 5
}
```

**Schedule follow-up**
```http
POST /api/email/schedule-followup
Authorization: Bearer <token>
Content-Type: application/json

{
  "contact_id": 1,
  "followup_date": "2025-10-20T10:00:00Z",
  "template_id": 1
}
```

### Dashboard

**Get dashboard stats**
```http
GET /api/dashboard/stats
Authorization: Bearer <token>
```

**Get activity logs**
```http
GET /api/dashboard/activity?page=1&page_size=20
Authorization: Bearer <token>
```

**Get pipeline overview**
```http
GET /api/dashboard/pipeline
Authorization: Bearer <token>
```

## Email Template Placeholders

Supported placeholders:
- `[ProfName]` - Professor's name
- `[ProfessorName]` - Professor's name (alternative)
- `[Name]` - Professor's name
- `[Email]` - Professor's email
- `[University]` - University name
- `[Department]` - Department name
- `[ResearchInterest]` - Research interests
- `[ResearchTopic]` - Research topic (alternative)
- `[Website]` - Professor's website

Example template:
```
Dear Professor [ProfName],

I am writing to express my interest in pursuing a PhD at [University] in [Department]. 
I am particularly interested in your research on [ResearchInterest]...
```

## AI Personalization

The system uses OpenAI GPT-4 to enhance email templates. When `use_ai=true`:

1. **Placeholder replacement**: First applies basic placeholder substitution
2. **AI enhancement**: Sends the template and contact info to GPT-4
3. **Personalized output**: Returns a more engaging, tailored email

Example:
- **Original**: "Dear Professor [ProfName], I am interested in your research on [ResearchInterest]..."
- **AI-Enhanced**: "Dear Professor Smith, I was fascinated by your recent publication on neural architecture search, particularly your novel approach to..."

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT secret key | Required |
| `DATABASE_URL` | Database connection string | `sqlite:///./thesislink.db` |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `SMTP_HOST` | SMTP server host | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USERNAME` | SMTP username | Required |
| `SMTP_PASSWORD` | SMTP password (app password) | Required |
| `SMTP_FROM_EMAIL` | Sender email | Required |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `MAX_UPLOAD_SIZE` | Max file upload size (bytes) | `10485760` (10MB) |
| `ALLOWED_FILE_TYPES` | Allowed file extensions | `.pdf,.doc,.docx,.txt` |
| `BATCH_EMAIL_DELAY_SECONDS` | Delay between batch emails | `5` |

### Gmail SMTP Setup

To use Gmail SMTP:

1. Enable 2-factor authentication on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the app password in `SMTP_PASSWORD`

## Testing

Run tests:
```bash
cd backend
pytest
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

## Deployment

### Heroku

1. Install Heroku CLI
2. Create app: `heroku create thesislink`
3. Add PostgreSQL: `heroku addons:create heroku-postgresql:mini`
4. Add Redis: `heroku addons:create heroku-redis:mini`
5. Set environment variables:
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set OPENAI_API_KEY=your-key
heroku config:set SMTP_USERNAME=your-email
heroku config:set SMTP_PASSWORD=your-password
```
6. Deploy: `git push heroku main`

### AWS / Cloud

The application is containerized and can be deployed to any cloud platform supporting Docker.

## Development Roadmap

### Phase 1: Backend MVP ✅ (Current)
- [x] Database models and schemas
- [x] Authentication system
- [x] Contact management CRUD
- [x] Template management
- [x] Email sending (SMTP)
- [x] AI personalization
- [x] File upload/download
- [x] Follow-up scheduling
- [x] Dashboard & analytics
- [x] Activity logging

### Phase 2: Frontend Development 🚧 (Next)
- [ ] React project setup with Vite
- [ ] TailwindCSS styling
- [ ] Authentication UI
- [ ] Contact management interface
- [ ] Template editor
- [ ] Email composer
- [ ] Dashboard with charts
- [ ] File upload UI

### Phase 3: Enhancements
- [ ] Gmail API integration
- [ ] Real-time notifications (WebSocket)
- [ ] Email reply tracking
- [ ] Advanced analytics
- [ ] Template library
- [ ] Mobile responsive design
- [ ] Dark mode

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License

## Support

For issues and questions:
- GitHub Issues: [Create an issue]
- Documentation: http://localhost:8000/api/docs

## Acknowledgments

- FastAPI for the excellent web framework
- OpenAI for GPT-4 API
- Celery for task scheduling
- All contributors and users

---

**Built with ❤️ for graduate students worldwide**
