# Project Specification: Task Management API

## Overview

Build a RESTful API for a task management system with user authentication, task CRUD operations, and basic project organization.

## Technology Stack

- **Runtime**: Node.js 18+
- **Framework**: Express.js
- **Language**: TypeScript
- **Database**: PostgreSQL
- **ORM**: Prisma
- **Authentication**: JWT
- **Validation**: Zod
- **Testing**: Jest
- **API Documentation**: Swagger/OpenAPI

## Requirements

### 1. Project Setup

- Initialize TypeScript project with Express
- Configure ESLint and Prettier
- Set up directory structure:
  ```
  src/
    controllers/
    models/
    routes/
    middleware/
    utils/
    config/
  tests/
  ```
- Create `.env` template with required variables
- Set up PostgreSQL connection via Prisma

### 2. Database Schema

**Users**:
- id (UUID, primary key)
- email (unique, required)
- password (hashed, required)
- name (required)
- created_at, updated_at

**Projects**:
- id (UUID, primary key)
- name (required)
- description (optional)
- owner_id (foreign key to Users)
- created_at, updated_at

**Tasks**:
- id (UUID, primary key)
- title (required)
- description (optional)
- status (enum: TODO, IN_PROGRESS, DONE)
- priority (enum: LOW, MEDIUM, HIGH)
- due_date (optional)
- project_id (foreign key to Projects)
- assigned_to (foreign key to Users)
- created_by (foreign key to Users)
- created_at, updated_at

### 3. API Endpoints

#### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/refresh` - Refresh JWT token

#### Users
- `GET /api/users/me` - Get current user profile
- `PATCH /api/users/me` - Update current user profile

#### Projects
- `GET /api/projects` - List all projects (user's projects)
- `POST /api/projects` - Create new project
- `GET /api/projects/:id` - Get project by ID
- `PATCH /api/projects/:id` - Update project
- `DELETE /api/projects/:id` - Delete project

#### Tasks
- `GET /api/tasks` - List all tasks (with filters)
  - Query params: `project_id`, `status`, `assigned_to`, `priority`
- `POST /api/tasks` - Create new task
- `GET /api/tasks/:id` - Get task by ID
- `PATCH /api/tasks/:id` - Update task
- `DELETE /api/tasks/:id` - Delete task

### 4. Authentication & Authorization

- Use JWT tokens for authentication
- Hash passwords with bcrypt (10 rounds)
- Implement middleware for:
  - Token validation
  - User authentication
  - Resource authorization (users can only access their own data)
- Token expiration: 1 hour (access token), 7 days (refresh token)

### 5. Validation

- Validate all request bodies using Zod schemas
- Return clear validation errors (400 status)
- Example validations:
  - Email format
  - Password minimum length (8 characters)
  - Required fields
  - Enum values

### 6. Error Handling

- Global error handling middleware
- Structured error responses:
  ```json
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Invalid input",
      "details": [...]
    }
  }
  ```
- HTTP status codes:
  - 200: Success
  - 201: Created
  - 400: Bad request
  - 401: Unauthorized
  - 403: Forbidden
  - 404: Not found
  - 500: Server error

### 7. Testing

- Unit tests for:
  - Controllers
  - Middleware
  - Utilities
- Integration tests for:
  - API endpoints
  - Database operations
- Test coverage goal: >80%
- Use in-memory SQLite for tests

### 8. API Documentation

- Generate Swagger/OpenAPI documentation
- Include:
  - Endpoint descriptions
  - Request/response schemas
  - Authentication requirements
  - Example requests
- Serve documentation at `/api/docs`

### 9. Configuration

- Environment variables:
  - `DATABASE_URL`
  - `JWT_SECRET`
  - `JWT_REFRESH_SECRET`
  - `PORT`
  - `NODE_ENV`
- Separate configs for development, test, production

### 10. Logging

- Use Winston for logging
- Log levels: error, warn, info, debug
- Log format: JSON for production, pretty for development
- Include:
  - Request ID
  - User ID (if authenticated)
  - Timestamp
  - HTTP method and path
  - Response time

## Deliverables

1. **Working API**: All endpoints functional and tested
2. **Database**: Prisma schema and migrations
3. **Tests**: Unit and integration tests with >80% coverage
4. **Documentation**:
   - README with setup instructions
   - API documentation (Swagger)
   - Environment variable template
5. **Code Quality**:
   - TypeScript with strict mode
   - ESLint configuration
   - Prettier formatting
   - No linting errors

## Non-Requirements (Out of Scope)

- Frontend/UI
- Email notifications
- File uploads
- Real-time updates (WebSockets)
- Task comments or attachments
- Team/organization management
- Rate limiting (can be added later)
- Caching

## Acceptance Criteria

- [ ] All API endpoints return correct responses
- [ ] Authentication works (register, login, token refresh)
- [ ] Users can only access their own data
- [ ] Database migrations run successfully
- [ ] All tests pass
- [ ] Test coverage >80%
- [ ] API documentation is complete
- [ ] Code follows TypeScript best practices
- [ ] No ESLint errors or warnings
- [ ] README includes clear setup instructions

## Estimated Complexity

- **Small**: 10-15 tasks
- **Time estimate**: 2-3 batches in GPT mode
- **Suitable for**: Demonstration of orchestrator capabilities
