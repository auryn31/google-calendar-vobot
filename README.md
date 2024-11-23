# Calendar API Integration

A full-stack application that provides Google Calendar integration with a clean web interface and a companion UI app for Vobot devices.

## Features

- OAuth2 authentication with Google Calendar API
- Real-time calendar event fetching
- Secure JWT token management
- Responsive web interface
- Vobot device integration with visual meeting indicators
- Docker containerization for easy deployment

## Architecture

### Backend (Node.js + TypeScript)
- Express.js server
- Google Calendar API integration
- Supabase database for token storage
- JWT authentication

### Frontend (HTML + CSS)
- Responsive single-page application
- Google Sign-in integration
- Real-time event display

### Vobot UI (MicroPython)
- Meeting status indicator
- LED color notifications
- Automatic event synchronization

## Prerequisites

- Node.js 18+ (LTS version)
- Docker and Docker Compose
- Supabase account
- Google Cloud Console project with Calendar API enabled
- Vobot MiniDock device (for UI component)

## Environment Variables

Create a `.env` file in the root directory:

```env
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback
JWT_SECRET=your_jwt_secret
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_key
```

## Database Setup

1. Create a Supabase project
2. Run the following SQL migration:

```sql
-- Create the user_auth table
CREATE TABLE user_auth (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL,
  google_tokens JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_auth_updated_at
    BEFORE UPDATE ON user_auth
    FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd calendar-api
```

2. Install dependencies:
```bash
yarn install
```

3. Build the TypeScript code:
```bash
yarn build
```

4. Create a `.env` file with required variables (see Environment Variables section)

## Development

Available scripts:
```bash
yarn dev    # Run development server with ts-node
yarn build  # Build TypeScript to dist/
yarn start  # Run built code from dist/
yarn watch  # Watch for TypeScript changes
```

## Docker Deployment

1. Build and tag the Docker image:
```bash
docker build -t your-username/vobot-calendar:latest .
```

2. Run with Docker Compose:
```bash
docker-compose up -d
```

Note: Make sure all environment variables are properly set in your environment or in a `.env` file before running docker-compose.

## Hosting Guide

### Backend Deployment

1. Push the Docker image to Docker Hub:
```bash
docker push your-username/vobot-calendar:latest
```

2. Deploy to your hosting platform:

#### Option 1: Digital Ocean
- Create a new App
- Connect to your Docker Hub repository
- Configure environment variables
- Deploy

#### Option 2: AWS ECS
- Create an ECS cluster
- Create a task definition using the Docker image
- Configure environment variables
- Launch service

### Database Hosting

The project uses Supabase, which provides a hosted PostgreSQL database:

1. Create a new Supabase project
2. Execute the SQL migration script
3. Update environment variables with new Supabase credentials

## Vobot Device Setup

### System Requirements
- Minimum Vobot version: 1.1.0
- Compatible devices: MiniDock only

1. Install the Vobot UI app following the manifest specifications in `vobot-ui/manifest.yml`
2. Configure the API URL and authentication token in the Vobot UI code

## API Documentation

### Authentication
- `GET /auth/google`: Initiates Google OAuth2 flow
- `GET /auth/google/callback`: OAuth2 callback handler

### Calendar Events
- `GET /calendar/events`: Fetch today's calendar events
  - Requires Authorization header with JWT token

## Security Considerations

- All sensitive data is stored in environment variables
- JWT tokens for API authentication
- Secure token storage in Supabase
- HTTPS required for production deployment

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
