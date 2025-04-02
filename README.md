# Task Management Backend

A robust Django REST API backend for managing tasks and boards with user collaboration features.

## Features

- User authentication and authorization
- Board management with member roles
- Task creation and assignment
- Task collaboration
- Board invitations system
- Calendar view for tasks
- Search and filtering capabilities

## Project Structure

```
task-management-back/
├── tasks/                 # Main app for task and board management
│   ├── models.py         # Database models for tasks, boards, and invitations
│   ├── views.py          # API endpoints and business logic
│   ├── serializers.py    # Data serialization for API responses
│   └── permissions.py    # Custom permission classes
├── users/                # User management app
├── task_management/      # Project configuration
│   ├── settings.py       # Django settings
│   ├── urls.py          # Main URL routing
│   └── wsgi.py          # WSGI configuration
├── manage.py            # Django management script
├── requirements.txt     # Project dependencies
├── Dockerfile          # Docker configuration
└── docker-compose.yml  # Docker Compose configuration
```

## Setup Instructions

### Local Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd task-management-back
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with:
```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Start the development server:
```bash
python manage.py runserver
```

### Docker Setup

1. Build and start the containers:
```bash
docker-compose up --build
```

2. The application will be available at http://localhost:8000

3. To stop the containers:
```bash
docker-compose down
```

4. To view logs:
```bash
docker-compose logs -f
```

## API Endpoints

### Authentication
- `POST /api/token/` - Get JWT token
- `POST /api/token/refresh/` - Refresh JWT token

### Boards
- `GET /api/boards/` - List all boards
- `POST /api/boards/` - Create a new board
- `GET /api/boards/{id}/` - Get board details
- `PUT /api/boards/{id}/` - Update board
- `DELETE /api/boards/{id}/` - Delete board
- `GET /api/boards/{id}/tasks/` - List board tasks
- `POST /api/boards/{id}/add_member/` - Add board member
- `POST /api/boards/{id}/remove_member/` - Remove board member

### Tasks
- `GET /api/tasks/` - List all tasks
- `POST /api/tasks/` - Create a new task
- `GET /api/tasks/{id}/` - Get task details
- `PUT /api/tasks/{id}/` - Update task
- `DELETE /api/tasks/{id}/` - Delete task
- `GET /api/tasks/calendar/` - Get tasks for calendar view
- `POST /api/tasks/{id}/add_collaborator/` - Add task collaborator

### Invitations
- `GET /api/invitations/` - List invitations
- `POST /api/invitations/invite/` - Send board invitation
- `POST /api/invitations/{id}/accept/` - Accept invitation
- `POST /api/invitations/{id}/decline/` - Decline invitation

## Dependencies

- Django 5.0.3
- Django REST Framework 3.14.0
- Django REST Framework SimpleJWT 5.3.0
- Django CORS Headers 4.3.1
- PostgreSQL (psycopg2-binary 2.9.9)
- Python-dotenv 1.0.0
- Pillow 10.2.0

