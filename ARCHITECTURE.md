# ThesisLink - Technical Architecture & Design Decisions

## Overview

ThesisLink is a full-stack web application designed to help graduate students manage their academic supervisor outreach process. This document explains the architectural decisions, design patterns, and implementation details.

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│   Frontend      │
│   (React +      │  ← To be implemented
│   TailwindCSS)  │
└────────┬────────┘
         │ HTTP/REST
         ↓
┌─────────────────┐
│   API Layer     │
│   (FastAPI)     │  ← Authentication, Routing
└────────┬────────┘
         │
    ┌────┴────┬─────────────┬──────────┐
    ↓         ↓             ↓          ↓
┌────────┐ ┌──────┐  ┌──────────┐ ┌──────────┐
│Service │ │ LLM  │  │  Email   │ │  File    │
│ Layer  │ │Service│  │ Service  │ │ Service  │
└────┬───┘ └──┬───┘  └────┬─────┘ └────┬─────┘
     │        │            │            │
     └────────┴─────┬──────┴────────────┘
                    ↓
            ┌───────────────┐
            │   Database    │
            │  (PostgreSQL) │
            └───────────────┘

┌──────────────────────────────────────┐
│        Background Jobs               │
│  ┌─────────┐      ┌──────────┐      │
│  │ Celery  │ ←──→ │  Redis   │      │
│  │ Worker  │      │  Broker  │      │
│  └─────────┘      └──────────┘      │
└──────────────────────────────────────┘
```

## Design Decisions

### 1. FastAPI Framework

**Why FastAPI?**
- **Performance**: Async support, one of the fastest Python frameworks
- **Type Safety**: Built-in Pydantic validation
- **Auto Documentation**: Swagger/ReDoc generated automatically
- **Modern**: Async/await support for I/O operations
- **Developer Experience**: Excellent error messages and type hints

**Alternative Considered**: Django REST Framework
- Rejected because FastAPI offers better performance and modern async features

### 2. Database Design

**Entity Relationship Diagram:**

```
┌─────────┐
│  User   │
└────┬────┘
     │ 1
     │
     │ *
     ├──────────────┬─────────────┬───────────────┐
     │              │             │               │
┌────┴────┐   ┌────┴─────┐  ┌───┴────┐   ┌─────┴──────┐
│ Contact │   │ Template │  │Document│   │ActivityLog │
└────┬────┘   └──────────┘  └───┬────┘   └────────────┘
     │ 1                         │ *
     │                           │
     │ *                         │
     └───────────────────────────┘
```

**Key Relationships:**
- User has many Contacts (1:N)
- User has many Templates (1:N)
- User has many Documents (1:N)
- Contact has many Documents (1:N)
- All entities log to ActivityLog for audit trail

**Why SQLAlchemy ORM?**
- Type-safe database operations
- Easy migrations with Alembic
- Support for multiple databases (SQLite, PostgreSQL)
- Relationship management

### 3. Authentication Strategy

**JWT (JSON Web Tokens)**

```python
# Flow:
1. User registers → Password hashed with bcrypt
2. User logs in → Credentials verified
3. Server generates JWT with user data
4. Client stores token
5. Client sends token in Authorization header
6. Server validates token on each request
```

**Why JWT over Sessions?**
- **Stateless**: No server-side session storage needed
- **Scalable**: Works across multiple servers
- **Mobile-Ready**: Easy to implement in mobile apps
- **Self-Contained**: Contains all user information

**Security Features:**
- Bcrypt password hashing (cost factor 12)
- Token expiration (30 minutes default)
- Password complexity requirements
- Protected routes with dependency injection

### 4. Service Layer Pattern

**Why Service Layer?**
```
Controller (API) → Service Layer → Database
```

Benefits:
- **Separation of Concerns**: Business logic separated from API routes
- **Reusability**: Services can be used by multiple endpoints
- **Testability**: Easy to mock and test
- **Maintainability**: Changes to business logic don't affect API layer

**Example:**
```python
# Bad (business logic in route):
@router.post("/contact")
def create_contact(data):
    contact = Contact(**data)
    db.add(contact)
    activity = ActivityLog(...)
    db.add(activity)
    db.commit()
    return contact

# Good (using service):
@router.post("/contact")
def create_contact(data):
    return ContactService.create(db, data)
```

### 5. AI Personalization Strategy

**Two-Tier Approach:**

1. **Basic Placeholder Replacement** (Free, Fast)
   - Replaces `[ProfName]`, `[University]`, etc.
   - No API cost
   - Instant response

2. **AI Enhancement** (OpenAI, Costs API credits)
   - Uses GPT-4 for intelligent personalization
   - Considers research interests
   - More natural, engaging emails
   - Fallback to basic if AI fails

**Why OpenAI GPT-4?**
- State-of-the-art language understanding
- Excellent at personalization tasks
- API is reliable and well-documented
- Can be easily swapped for other LLMs

**Design Pattern:**
```python
async def personalize_template(template, contact, use_ai=False):
    # Always do basic replacement first
    basic = replace_placeholders(template, contact)
    
    if not use_ai:
        return basic
    
    try:
        # Enhance with AI
        return await ai_enhance(basic, contact)
    except Exception:
        # Fallback to basic if AI fails
        return basic
```

### 6. Email Sending Architecture

**SMTP vs Gmail API:**

Currently implemented: **SMTP with aiosmtplib**

**Why SMTP?**
- Simple to set up (just need app password)
- Works with any email provider
- Async support with aiosmtplib
- No OAuth complexity

**Gmail API (Planned):**
- Better deliverability
- Access to inbox for reply tracking
- No SMTP port issues
- OAuth2 authentication

**Batch Email Strategy:**
```python
# Sequential sending with delays
for recipient in recipients:
    send_email(recipient)
    await asyncio.sleep(delay)  # Prevent spam detection
```

**Why delays between emails?**
- Avoids triggering spam filters
- More natural sending pattern
- Configurable per user needs

### 7. File Upload System

**Storage Strategy: Local Filesystem**

```
uploads/
├── user_1/
│   ├── cv_20251011_143022.pdf
│   └── sop_20251011_144533.docx
├── user_2/
│   └── transcript_20251011_145644.pdf
```

**Why local filesystem?**
- Simple to implement
- No cloud storage costs (MVP)
- Easy to migrate to S3/Cloud Storage later

**Security Measures:**
1. File type validation (whitelist)
2. File size limits (10MB default)
3. Filename sanitization (prevent path traversal)
4. Unique filenames (timestamp-based)
5. User-isolated directories

**Future: Cloud Storage**
```python
# Easy to swap:
class FileService:
    def save_file(self, file):
        if settings.STORAGE_TYPE == "s3":
            return self._save_to_s3(file)
        else:
            return self._save_to_local(file)
```

### 8. Task Scheduling with Celery

**Architecture:**

```
┌──────────────┐
│   FastAPI    │
│   (Creates   │
│   scheduled  │
│   tasks)     │
└──────┬───────┘
       │
       ↓
┌──────────────┐     ┌──────────────┐
│    Redis     │ ←─→ │Celery Worker │
│   (Broker)   │     │ (Executes    │
│              │     │  tasks)      │
└──────┬───────┘     └──────────────┘
       ↑
       │
┌──────┴───────┐
│ Celery Beat  │
│ (Scheduler)  │
│ Checks every │
│ hour         │
└──────────────┘
```

**Why Celery?**
- Industry standard for Python background jobs
- Reliable task queue
- Scheduled tasks (Beat)
- Retry mechanisms
- Easy to monitor

**Follow-Up Flow:**
1. User schedules follow-up for contact
2. Record saved in database with `follow_up_date`
3. Celery Beat checks every hour for due follow-ups
4. When found, creates task for Celery Worker
5. Worker sends email and updates database

### 9. Activity Logging

**Why comprehensive logging?**
- **Audit Trail**: Track all user actions
- **Debugging**: Understand what went wrong
- **Analytics**: Show user their activity history
- **Compliance**: Required for some use cases

**What we log:**
- Contact creation/updates
- Email sent/failed
- Documents uploaded
- Templates created/used
- Follow-ups scheduled

**Storage:**
```python
ActivityLog:
    - type: Enum (EMAIL_SENT, CONTACT_CREATED, etc.)
    - title: Short description
    - description: Detailed info
    - metadata: JSON for flexible additional data
    - timestamp: When it happened
```

### 10. API Design Principles

**RESTful Design:**
```
GET    /api/contacts        → List contacts
POST   /api/contacts        → Create contact
GET    /api/contacts/:id    → Get one contact
PUT    /api/contacts/:id    → Update contact
DELETE /api/contacts/:id    → Delete contact
```

**Response Format:**
```json
{
  "data": { ... },
  "message": "Success",
  "status": 200
}
```

**Error Format:**
```json
{
  "detail": "Error message",
  "status": 400
}
```

**Pagination:**
```json
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "items": [...]
}
```

## Code Organization

### Layer Structure

```
1. API Layer (app/api/)
   - Route handlers
   - Request validation
   - Response formatting
   - Dependency injection

2. Service Layer (app/services/)
   - Business logic
   - Data validation
   - External API calls
   - Complex operations

3. Model Layer (app/models/)
   - Database schema
   - Relationships
   - Constraints

4. Schema Layer (app/schemas/)
   - Pydantic models
   - Input validation
   - Output serialization

5. Utils Layer (app/utils/)
   - Helper functions
   - Security utilities
   - Common operations
```

### Dependency Injection

FastAPI's dependency injection for clean code:

```python
@router.get("/contacts")
async def list_contacts(
    current_user: User = Depends(get_current_user),  # Auth
    db: Session = Depends(get_db),                   # Database
    page: int = Query(1, ge=1)                       # Validation
):
    return ContactService.list(db, current_user.id, page)
```

## Performance Considerations

### 1. Async/Await
```python
# I/O operations are async
async def send_email(...):
    await aiosmtplib.send(...)

# Database queries stay sync (SQLAlchemy ORM)
def get_user(db, user_id):
    return db.query(User).filter(User.id == user_id).first()
```

### 2. Database Query Optimization
- Eager loading with `joinedload` to avoid N+1 queries
- Indexes on frequently queried fields (email, status)
- Pagination to limit result sets

### 3. Caching (Future)
```python
# Redis for caching
@cache(expire=300)  # 5 minutes
def get_dashboard_stats(user_id):
    # Expensive query
    return stats
```

## Security Measures

1. **Authentication**: JWT with secure secret
2. **Password Hashing**: Bcrypt with salt
3. **Input Validation**: Pydantic schemas
4. **SQL Injection**: SQLAlchemy ORM (parameterized queries)
5. **CORS**: Configured for specific origins
6. **File Upload**: Type and size validation
7. **Rate Limiting**: (To be implemented)
8. **HTTPS**: Required in production

## Testing Strategy

### Test Pyramid

```
        /\
       /UI\          ← Few (Future: Frontend tests)
      /────\
     /Inte-\         ← Some (API integration tests)
    / gration\
   /──────────\
  /   Unit     \     ← Many (Service, utility tests)
 /──────────────\
```

**Current Tests:**
- Unit tests for services
- Authentication tests
- Database model tests

**Future Tests:**
- API endpoint tests
- Integration tests
- Frontend component tests

## Scalability Considerations

### Horizontal Scaling

**Current**: Single server
**Future**: Multiple servers with load balancer

```
           Load Balancer
                 │
        ┌────────┼────────┐
        ↓        ↓        ↓
    Server 1  Server 2  Server 3
        │        │        │
        └────────┼────────┘
                 ↓
          PostgreSQL + Redis
```

**Requirements:**
- Stateless API (✓ JWT authentication)
- Shared database (✓ PostgreSQL)
- Shared file storage (→ Move to S3)
- Centralized Redis (✓ Already external)

### Database Scaling

**Current**: Single PostgreSQL instance
**Future**: 
- Read replicas for queries
- Master for writes
- Connection pooling

### Caching Strategy

**Future Implementation:**
```python
# Redis caching
- User sessions
- Dashboard statistics (expensive queries)
- Template data
- Contact lists

# Cache invalidation
- On data updates
- Time-based expiry
- LRU eviction
```

## Monitoring & Observability

**To Implement:**
1. **Logging**: Structured logging with levels
2. **Metrics**: Prometheus for metrics
3. **Tracing**: OpenTelemetry for distributed tracing
4. **Alerting**: Alert on errors/performance issues

## Future Enhancements

### 1. Real-time Features
- WebSocket for live notifications
- Real-time dashboard updates
- Live email status updates

### 2. Advanced Analytics
- Machine learning for optimal send times
- Response prediction
- A/B testing for email templates

### 3. Integration Ecosystem
- Google Scholar API for professor research
- LinkedIn integration
- University database imports
- Calendar integration (Google/Outlook)

### 4. Mobile App
- React Native app
- Push notifications
- Offline support

## Conclusion

ThesisLink is designed with:
- **Modularity**: Easy to extend and modify
- **Scalability**: Ready to grow with user base
- **Security**: Best practices implemented
- **Developer Experience**: Clean, well-documented code
- **User Experience**: Fast, reliable, and intuitive

The architecture supports rapid feature development while maintaining code quality and system reliability.
