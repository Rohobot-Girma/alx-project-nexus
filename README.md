# ProDev Backend Engineering Journey

##  Project Objective

This repository documents my journey through the **ProDev Backend Engineering Program**. It serves as:

* A **reference guide** for key backend technologies, concepts, and tools.
* A **record of challenges and solutions** I faced along the way.
* A **collaboration hub** with both frontend and backend learners.
* A way to **consolidate learnings** for future growth.


##  Key Technologies Learned

* **Python** – Core programming language for backend development.
* **Django** – High-level Python web framework for building scalable apps.
* **Django REST Framework (DRF)** – For building RESTful APIs.
* **GraphQL** – Alternative to REST, enabling flexible and efficient data queries.
* **Docker** – Containerization for consistent deployment.
* **CI/CD Pipelines** – Automating build, test, and deployment processes.

##  Important Backend Development Concepts

1. **Database Design & Management** – Designing schemas, relationships, and queries (PostgreSQL, MySQL).
2. **Asynchronous Programming** – Using async features for concurrency and better performance.
3. **Caching Strategies** – Redis/memory caching to improve response times.
4. **Message Queues** – RabbitMQ and Celery for task scheduling and background jobs.
5. **System Design** – Structuring scalable and reliable backend systems.

##  Challenges & Solutions

### 1. Setting up CI/CD for the first time

* **Challenge:** Difficulty automating build and deployment.
* **Solution:** Learned GitHub Actions & automated testing workflows.

### 2. Debugging complex API integration with frontend

* **Challenge:** Mismatched data between frontend and backend.
* **Solution:** Used Postman and DRF browsable API to test endpoints thoroughly.

### 3. Managing asynchronous tasks with Celery & RabbitMQ

* **Challenge:** Long-running background tasks failing.
* **Solution:** Broke tasks into smaller units and used monitoring tools (Flower) to track execution.

### 4. Dockerizing Django apps with proper networking

* **Challenge:** Database container not connecting with the app.
* **Solution:** Used Docker Compose to manage containers for app + database + cache.


##  Best Practices & Personal Takeaways

* Write clean, modular code (follow PEP8 and Django best practices).
* Test everything – unit tests, integration tests, API endpoint tests.
* Use version control properly – commit often, write meaningful commit messages.
* Collaborate effectively – share API docs clearly for frontend learners.
* Think scalability early – plan for caching, load balancing, and async tasks.
* Keep learning – backend engineering is an evolving field; continuous learning is key.

##  Collaboration

### Who I Collaborated With

* **Backend learners** – Peer reviews.

### Where We Collaborated

* **Discord Channel:** `#ProDevProjectNexus` – For sharing ideas, solving blockers, and keeping up with staff announcements.


##  Next Steps

1. Contribute to open-source backend projects.
2. Deepen knowledge of **system design & scalability**.
3. Explore **microservices architecture** with Django + FastAPI.
4. Mentor future ProDev learners.

# Movie Recommendation App Backend

A robust Django backend for a Movie Recommendation App with TMDb integration, JWT authentication, Redis caching, and comprehensive API documentation.

##  Features

- **Movie API Integration**: Fetch trending and popular movies from TMDb API
- **User Authentication**: JWT-based authentication with user registration/login
- **Personalized Recommendations**: AI-powered movie recommendations based on user preferences
- **User Favorites**: Save and manage favorite movies
- **Movie Ratings & Reviews**: Rate and review movies
- **Redis Caching**: Performance optimization with Redis caching
- **API Documentation**: Comprehensive Swagger/OpenAPI documentation
- **Database Optimization**: PostgreSQL with optimized queries

##  Tech Stack

- **Backend**: Django 4.2.7, Django REST Framework
- **Database**: PostgreSQL
- **Cache**: Redis
- **Authentication**: JWT (SimpleJWT)
- **API Documentation**: Swagger/OpenAPI (drf-yasg)
- **External API**: TMDb API
- **Testing**: pytest, pytest-django

##  Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- TMDb API Key (Get one at [TMDb](https://www.themoviedb.org/settings/api))

##  Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd alx-project-nexus
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```bash
cp env.example .env
```

Edit `.env` with your configuration:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_ENGINE=django.db.backends.postgresql
DB_NAME=movie_recommendation_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://localhost:6379/1

# TMDb API Configuration
TMDB_API_KEY=your-tmdb-api-key-here
TMDB_BASE_URL=https://api.themoviedb.org/3

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440
```

### 5. Database Setup

Create PostgreSQL database:

```sql
CREATE DATABASE movie_recommendation_db;
```

Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Sync Initial Data

```bash
# Sync genres and initial movie data from TMDb
python manage.py sync_tmdb_data --genres --pages 3
```

### 8. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

##  API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/

##  API Endpoints

### Authentication
- `POST /api/users/register/` - User registration
- `POST /api/users/login/` - User login
- `POST /api/users/logout/` - User logout
- `GET /api/users/profile/` - Get user profile
- `PATCH /api/users/profile/` - Update user profile
- `GET /api/users/preferences/` - Get user preferences
- `PATCH /api/users/preferences/` - Update user preferences

### Movies
- `GET /api/movies/trending/` - Get trending movies
- `GET /api/movies/popular/` - Get popular movies
- `GET /api/movies/search/` - Search movies
- `GET /api/movies/list/` - List movies with filtering
- `GET /api/movies/{tmdb_id}/` - Get movie details
- `GET /api/movies/genres/` - Get all genres

### User Favorites & Ratings
- `GET /api/movies/favorites/` - Get user favorites
- `POST /api/movies/favorites/` - Add movie to favorites
- `DELETE /api/movies/favorites/{id}/remove/` - Remove from favorites
- `POST /api/movies/rate/` - Rate a movie
- `GET /api/movies/ratings/` - Get user ratings

### Recommendations
- `GET /api/recommendations/personalized/` - Get personalized recommendations
- `GET /api/recommendations/trending/` - Get trending recommendations
- `POST /api/recommendations/track-interaction/` - Track user interaction

### JWT Authentication
- `POST /api/auth/token/` - Get access token
- `POST /api/auth/token/refresh/` - Refresh access token

##  Testing

Run tests:

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test users
python manage.py test movies
python manage.py test recommendations

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

##  Management Commands

### Sync TMDb Data

```bash
# Sync trending and popular movies (5 pages each)
python manage.py sync_tmdb_data

# Sync specific categories
python manage.py sync_tmdb_data --categories trending popular --pages 10

# Also sync genres
python manage.py sync_tmdb_data --genres
```

##  Project Structure

```
movie_recommendation/
├── movie_recommendation/          # Main Django project
│   ├── settings.py               # Django settings
│   ├── urls.py                   # Main URL configuration
│   └── wsgi.py                   # WSGI configuration
├── users/                        # User management app
│   ├── models.py                 # User model
│   ├── serializers.py            # User serializers
│   ├── views.py                  # User views
│   ├── urls.py                   # User URLs
│   └── tests.py                  # User tests
├── movies/                       # Movies app
│   ├── models.py                 # Movie, Genre, Rating models
│   ├── serializers.py            # Movie serializers
│   ├── views.py                  # Movie views
│   ├── services.py               # TMDb API service
│   ├── urls.py                   # Movie URLs
│   ├── management/               # Management commands
│   │   └── commands/
│   │       └── sync_tmdb_data.py
│   └── tests.py                  # Movie tests
├── recommendations/              # Recommendations app
│   ├── models.py                 # Recommendation models
│   ├── serializers.py            # Recommendation serializers
│   ├── views.py                  # Recommendation views
│   ├── urls.py                   # Recommendation URLs
│   └── tests.py                  # Recommendation tests
├── requirements.txt              # Python dependencies
├── env.example                   # Environment variables example
└── README.md                     # This file
```

##  Deployment

### Production Settings

For production deployment:

1. Set `DEBUG=False` in environment variables
2. Configure production database
3. Set up Redis server
4. Configure static file serving
5. Set up SSL certificates
6. Configure proper logging

### Docker Deployment (Optional)

```dockerfile
# Dockerfile example
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "movie_recommendation.wsgi:application", "--bind", "0.0.0.0:8000"]
```

##  Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run tests and ensure they pass
6. Submit a pull request



##  Support

For support and questions:

1. Check the API documentation at `/api/docs/`
2. Review the test files for usage examples
3. Check the Django logs for debugging information

##  API Usage Examples

### User Registration

```bash
curl -X POST http://localhost:8000/api/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepass123",
    "password_confirm": "securepass123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Get Trending Movies

```bash
curl -X GET "http://localhost:8000/api/movies/trending/?page=1&time_window=week"
```

### Search Movies

```bash
curl -X GET "http://localhost:8000/api/movies/search/?query=avengers&page=1"
```

### Add to Favorites (Authenticated)

```bash
curl -X POST http://localhost:8000/api/movies/favorites/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"movie_id": 123}'
```

##  Performance Features

- **Redis Caching**: All API responses are cached for better performance
- **Database Optimization**: Optimized queries with select_related and prefetch_related
- **Pagination**: All list endpoints support pagination
- **Background Tasks**: Movie data syncing can be run as background tasks
- **Connection Pooling**: Database connection pooling for better performance