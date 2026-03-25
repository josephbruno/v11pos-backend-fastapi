# FastAPI POS System

A modern Point of Sale (POS) system built with FastAPI, MySQL, and JWT authentication.

## Tech Stack

- **FastAPI** - Modern, fast web framework for building APIs
- **MySQL** - Relational database (localhost for dev, remote for prod)
- **SQLAlchemy (Async)** - Async ORM for database operations
- **Pydantic v2** - Data validation and settings management
- **JWT** - Access + Refresh token authentication
- **Alembic** - Database migrations
- **Docker & Docker Compose** - Containerization

## Project Structure

```
app/
├── main.py                 # FastAPI application entry point
├── core/
│   ├── config.py          # Environment-based configuration
│   ├── database.py        # MySQL async connection
│   ├── security.py        # JWT token logic
│   ├── dependencies.py    # Auth dependencies
│   └── response.py        # Standard API response helpers
├── modules/
│   ├── auth/              # Authentication module
│   │   ├── model.py
│   │   ├── schema.py
│   │   ├── service.py
│   │   └── route.py
│   └── user/              # User management module
│       ├── model.py
│       ├── schema.py
│       ├── service.py
│       └── route.py
├── migrations/            # Alembic migrations
└── tests/                 # Test files
```

## Setup Instructions

### 1. Local Development (without Docker)

#### Prerequisites
- Python 3.11+
- MySQL 8.0+

#### Steps

1. **Clone the repository**
```bash
cd /home/brunodoss/docs/pos/pos/pos-fastapi
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
- Copy `.env` and update if needed
- Ensure MySQL is running on localhost:3306
- Create database: `CREATE DATABASE fastapi_dev;`

5. **Run migrations**
```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

6. **Run the application**
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### 2. Docker Development

#### Prerequisites
- Docker
- Docker Compose

#### Steps

1. **Start services**
```bash
docker-compose up -d
```

2. **Run migrations** (inside container)
```bash
docker-compose exec fastapi alembic revision --autogenerate -m "Initial migration"
docker-compose exec fastapi alembic upgrade head
```

3. **View logs**
```bash
docker-compose logs -f fastapi
```

4. **Stop services**
```bash
docker-compose down
```

## API Documentation

Once the application is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Standard API Response Format

All API endpoints return responses in this format:

### Success Response
```json
{
  "success": true,
  "message": "User created successfully",
  "data": {...},
  "error": null
}
```

### Error Response
```json
{
  "success": false,
  "message": "Validation failed",
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "details": "Email already exists"
  }
}
```

## API Endpoints

### Authentication

- `POST /auth/login` - Login with email and password
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout (client-side token removal)

### Users

- `POST /users` - Create new user (public)
- `GET /users` - Get all users (requires auth)
- `GET /users/me` - Get current user info (requires auth)
- `GET /users/{user_id}` - Get user by ID (requires auth)
- `PUT /users/{user_id}` - Update user (requires auth)
- `DELETE /users/{user_id}` - Delete user (requires superuser)

## Environment Variables

### Development (.env)
```env
APP_ENV=development
DB_HOST=localhost
DB_PORT=3306
DB_NAME=fastapi_dev
DB_USER=root
DB_PASSWORD=root

JWT_SECRET=supersecret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Production (.env.prod)
Update with your production MySQL credentials and secure JWT secret.

## Database Migrations

### Create a new migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback migration
```bash
alembic downgrade -1
```

## Testing

Run tests with pytest:
```bash
pytest tests/
```

## Production Deployment

1. Update `.env.prod` with production credentials
2. Build Docker image:
```bash
docker build -t fastapi-pos:latest .
```

3. Deploy using Docker Compose or your preferred orchestration tool

## Security Notes

- Change `JWT_SECRET` in production to a strong, random value
- Use HTTPS in production
- Update CORS settings in `main.py` for production
- Never commit `.env` files to version control

## License

MIT
