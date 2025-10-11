# ThesisLink Development Guide

## Getting Started

### First Time Setup

1. **Clone and setup environment**
```powershell
cd ThesisLink
.\quickstart.ps1
```

2. **Configure environment variables**
Edit `backend\.env`:
```env
SECRET_KEY=generate-a-secure-random-key
OPENAI_API_KEY=sk-...your-key-here
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
```

3. **Start development servers**

Terminal 1 - Backend API:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Terminal 2 - Celery Worker:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
celery -A app.services.scheduler_service.celery_app worker --loglevel=info --pool=solo
```

Terminal 3 - Celery Beat:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
celery -A app.services.scheduler_service.celery_app beat --loglevel=info
```

## Development Workflow

### Making Changes

1. **Create a feature branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**
- Write code following project conventions
- Add docstrings to functions
- Update tests

3. **Format code**
```bash
black app/
isort app/
```

4. **Run tests**
```bash
pytest
```

5. **Commit and push**
```bash
git add .
git commit -m "Add: your feature description"
git push origin feature/your-feature-name
```

### Code Style Guidelines

**Python (Backend)**

```python
# Use type hints
def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Create a new user.
    
    Args:
        db: Database session
        user_data: User creation data
        
    Returns:
        Created user object
    """
    pass

# Use descriptive variable names
user_email = "test@example.com"  # Good
e = "test@example.com"           # Bad

# Keep functions focused
def send_email(to: str, subject: str, body: str):  # Good - single responsibility
    pass

def send_email_and_log_and_update_contact():  # Bad - too many responsibilities
    pass
```

**Naming Conventions**

- Classes: `PascalCase` (UserService, ContactModel)
- Functions: `snake_case` (get_user, send_email)
- Constants: `UPPER_SNAKE_CASE` (MAX_FILE_SIZE, API_VERSION)
- Private: `_prefixed` (_internal_function)

## Database Migrations

### Creating a Migration

When you change database models:

```bash
# Create migration
alembic revision --autogenerate -m "Add new field to user"

# Review the migration file in alembic/versions/

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Common Migration Commands

```bash
# View current version
alembic current

# View migration history
alembic history

# Upgrade to specific version
alembic upgrade <revision>

# Downgrade to specific version
alembic downgrade <revision>
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_auth.py::test_create_user

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Writing Tests

```python
# tests/test_feature.py
import pytest
from app.services.your_service import YourService

def test_your_feature(db_session):
    """Test description."""
    # Arrange
    input_data = {...}
    
    # Act
    result = YourService.your_method(db_session, input_data)
    
    # Assert
    assert result.field == expected_value
```

### Test Database

Tests use a separate SQLite database that's created and destroyed for each test:

```python
@pytest.fixture
def db_session():
    """Create fresh database for each test."""
    # Setup
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    yield db
    
    # Teardown
    db.close()
    Base.metadata.drop_all(bind=engine)
```

## Debugging

### Using Print Statements

```python
# Simple debugging
print(f"User ID: {user.id}, Email: {user.email}")

# Better: Use logging
import logging
logger = logging.getLogger(__name__)
logger.info(f"User {user.id} logged in")
```

### Using Python Debugger (pdb)

```python
def some_function():
    # Add breakpoint
    import pdb; pdb.set_trace()
    
    # Code will pause here
    result = complex_operation()
    return result
```

**pdb Commands:**
- `n` - Next line
- `s` - Step into function
- `c` - Continue
- `p variable` - Print variable
- `l` - List code
- `q` - Quit

### VS Code Debugging

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "jinja": true,
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

## API Testing

### Using Swagger UI

1. Start the server
2. Open http://localhost:8000/api/docs
3. Click "Authorize" and enter JWT token
4. Test endpoints interactively

### Using curl

```bash
# Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"password123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123"

# Use token
curl -X GET http://localhost:8000/api/contacts \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Using Python requests

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000/api"

# Register
response = requests.post(
    f"{BASE_URL}/auth/register",
    json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123"
    }
)
print(response.json())

# Login
response = requests.post(
    f"{BASE_URL}/auth/login",
    data={
        "username": "testuser",
        "password": "password123"
    }
)
token = response.json()["access_token"]

# Use token
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/contacts", headers=headers)
print(response.json())
```

## Common Issues & Solutions

### Issue: Celery won't start on Windows

**Solution**: Use `--pool=solo` flag
```bash
celery -A app.services.scheduler_service.celery_app worker --pool=solo --loglevel=info
```

### Issue: Database locked error (SQLite)

**Solution**: 
- Use PostgreSQL for concurrent access
- Or set `connect_args={"check_same_thread": False}` (already done)

### Issue: Import errors

**Solution**: Make sure you're in the right directory and venv is activated
```bash
cd backend
.\venv\Scripts\Activate.ps1
python -c "import app; print('OK')"
```

### Issue: SMTP authentication failed

**Solutions**:
1. Use Gmail App Password (not regular password)
2. Enable "Less secure app access" (not recommended)
3. Check SMTP settings in .env

### Issue: Redis connection refused

**Solution**: Start Redis server
```bash
# Windows (with Redis installed)
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:alpine
```

## Environment Variables

### Required Variables

```env
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=sk-your-key
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
```

### Generating SECRET_KEY

```python
import secrets
print(secrets.token_urlsafe(32))
```

### Gmail App Password

1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer"
3. Generate password
4. Use in SMTP_PASSWORD

## Performance Tips

### Database Queries

```python
# Bad - N+1 query problem
contacts = db.query(Contact).all()
for contact in contacts:
    print(contact.documents)  # Each iteration queries DB

# Good - Eager loading
from sqlalchemy.orm import joinedload
contacts = db.query(Contact).options(
    joinedload(Contact.documents)
).all()
```

### Async Operations

```python
# Use async for I/O operations
async def send_multiple_emails(emails):
    tasks = [send_email(email) for email in emails]
    await asyncio.gather(*tasks)  # Parallel execution
```

### Caching (Future)

```python
# Cache expensive operations
from functools import lru_cache

@lru_cache(maxsize=128)
def get_template_placeholders(template_text):
    return extract_placeholders(template_text)
```

## Code Review Checklist

Before submitting PR:

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New code has tests
- [ ] Docstrings added to functions
- [ ] No commented-out code
- [ ] No print statements (use logging)
- [ ] Error handling implemented
- [ ] Environment variables documented
- [ ] README updated if needed
- [ ] No sensitive data in code

## Useful Commands

### Database

```bash
# Reset database (DEV ONLY!)
rm thesislink.db
python -c "from app.database import init_db; init_db()"

# Or use Alembic
alembic downgrade base
alembic upgrade head
```

### Dependencies

```bash
# Add new dependency
pip install package-name
pip freeze > requirements.txt

# Update dependency
pip install --upgrade package-name
pip freeze > requirements.txt
```

### Docker

```bash
# Build and start
docker-compose up --build

# View logs
docker-compose logs -f backend

# Stop all
docker-compose down

# Remove volumes (reset DB)
docker-compose down -v

# Rebuild single service
docker-compose up --build backend
```

## Next Steps for Development

### Immediate TODOs

1. **Add more tests**
   - Contact service tests
   - Email service tests
   - Template personalization tests

2. **Implement rate limiting**
   - Use slowapi or FastAPI-Limiter
   - Protect auth endpoints

3. **Add logging**
   - Structured logging with loguru
   - Log rotation
   - Error tracking (Sentry)

4. **Frontend Development**
   - Set up React + Vite
   - Install TailwindCSS
   - Create component library
   - Implement authentication flow

### Feature Roadmap

**Phase 1 (Current)**: Backend MVP ✅
**Phase 2**: Frontend UI 🚧
**Phase 3**: Gmail API Integration
**Phase 4**: Advanced Analytics
**Phase 5**: Mobile App

## Resources

### Documentation

- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Celery: https://docs.celeryproject.org/
- Pydantic: https://docs.pydantic.dev/

### Learning Resources

- FastAPI Tutorial: https://fastapi.tiangolo.com/tutorial/
- Python Type Hints: https://docs.python.org/3/library/typing.html
- REST API Design: https://restfulapi.net/

### Community

- FastAPI Discord: https://discord.gg/fastapi
- Stack Overflow: Tag `fastapi`
- GitHub Discussions: (your repo)

## Getting Help

1. **Check documentation**: README.md and ARCHITECTURE.md
2. **Search issues**: GitHub Issues
3. **Ask in discussions**: GitHub Discussions
4. **Stack Overflow**: Tag with `fastapi`, `python`

## Contributing

See CONTRIBUTING.md for guidelines on:
- Code of conduct
- How to contribute
- Pull request process
- Issue reporting

---

Happy coding! 🚀
