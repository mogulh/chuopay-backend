# Chuopay - School Contribution Management Platform

A comprehensive school contribution management platform designed to simplify how schools request, collect, and track payments from parents. Built with Django/DRF backend and React/Next.js frontend.

## 🚀 Features

### Core Features

- **Group-Based Student Management** - Organize students into customizable groups
- **Admin-Initiated Contribution Requests** - Create contribution events with tiers and rules
- **Parent Contribution Dashboard** - View and pay contributions for children
- **Payment Tracking and Status** - Comprehensive payment status management
- **SMS Reminders and Notifications** - Automated and manual reminder system
- **Co-Parenting Support** - Multiple parents per student and multi-school support
- **Role-Based Access Control** - Admin, teacher, and parent roles

### Technical Stack

- **Backend**: Django 5.2 + Django REST Framework
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **Database**: PostgreSQL
- **Authentication**: Firebase Authentication (phone-based)
- **SMS**: Twilio/Africa's Talking integration
- **Payments**: MPESA STK Push integration
- **Background Tasks**: Celery + Redis
- **Containerization**: Docker + Docker Compose

## 📋 Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- PostgreSQL (for local development)

## 🛠️ Installation

### Using Docker (Recommended)

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd chuopay
   ```

2. **Set up environment variables**

   ```bash
   cp backend/env.example backend/.env
   # Edit backend/.env with your configuration
   ```

3. **Start the application**

   ```bash
   docker-compose up --build
   ```

4. **Run migrations**

   ```bash
   docker-compose exec backend python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

### Local Development

1. **Backend Setup**

   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp env.example .env
   # Edit .env with your configuration
   python manage.py migrate
   python manage.py runserver
   ```

2. **Frontend Setup**

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Start Redis and PostgreSQL**
   ```bash
   # Using Docker
   docker run -d -p 6379:6379 redis:7-alpine
   docker run -d -p 5432:5432 -e POSTGRES_DB=chuopay_db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=password postgres:15
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory with the following variables:

```env
# Django Settings
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings
DB_NAME=chuopay_db
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Firebase Settings
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789
FIREBASE_APP_ID=your_app_id

# SMS Gateway Settings
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# MPESA Settings
MPESA_CONSUMER_KEY=your_mpesa_consumer_key
MPESA_CONSUMER_SECRET=your_mpesa_consumer_secret
MPESA_BUSINESS_SHORT_CODE=your_business_short_code
MPESA_PASSKEY=your_mpesa_passkey
MPESA_ENVIRONMENT=sandbox
```

## 🏗️ Project Structure

```
chuopay/
├── backend/                 # Django backend
│   ├── accounts/           # User authentication app
│   ├── contributions/      # Contribution management app
│   ├── notifications/      # SMS notifications app
│   ├── chuopay_backend/   # Django project settings
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Backend container
├── frontend/              # Next.js frontend
│   ├── src/
│   │   ├── app/          # Next.js app router
│   │   ├── components/   # React components
│   │   └── lib/          # Utility functions
│   ├── package.json      # Node.js dependencies
│   └── Dockerfile        # Frontend container
├── docker-compose.yml    # Multi-container setup
└── README.md            # This file
```

## 🚀 Development

### Backend Development

```bash
cd backend
source venv/bin/activate
python manage.py runserver
```

### Frontend Development

```bash
cd frontend
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
python manage.py test

# Frontend tests
cd frontend
npm test
```

### Database Management

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

## 📱 API Endpoints

### Authentication

- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration
- `POST /api/auth/logout/` - User logout

### Groups

- `GET /api/groups/` - List groups
- `POST /api/groups/` - Create group
- `GET /api/groups/{id}/` - Get group details
- `PUT /api/groups/{id}/` - Update group
- `DELETE /api/groups/{id}/` - Delete group

### Students

- `GET /api/students/` - List students
- `POST /api/students/` - Create student
- `GET /api/students/{id}/` - Get student details
- `PUT /api/students/{id}/` - Update student
- `DELETE /api/students/{id}/` - Delete student

### Contributions

- `GET /api/contributions/` - List contributions
- `POST /api/contributions/` - Create contribution
- `GET /api/contributions/{id}/` - Get contribution details
- `PUT /api/contributions/{id}/` - Update contribution
- `DELETE /api/contributions/{id}/` - Delete contribution

## 🔐 Security

- All API endpoints require authentication
- Role-based access control implemented
- CORS configured for frontend communication
- Environment variables for sensitive data
- Input validation and sanitization

## 📊 Monitoring

- Celery worker monitoring for background tasks
- Database connection monitoring
- API response time monitoring
- Error logging and tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support, please contact the development team or create an issue in the repository.
