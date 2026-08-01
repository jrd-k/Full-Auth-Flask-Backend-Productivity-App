# Full Auth Flask Backend Productivity App

A secure Flask REST API for managing personal notes with session-based authentication, user ownership, CRUD routes, and paginated listing.

## Installation

```bash
pipenv install --dev
pipenv shell
```

## Database setup

```bash
flask db init
flask db migrate -m "initial migration"
flask db upgrade
python seed.py
```

## Run the app

```bash
python app.py
```

## Endpoints

- POST /signup: create a new user account
- POST /login: authenticate a user and start a session
- POST /logout: clear the current session
- GET /me: return the authenticated user
- GET /notes: list the current user's notes with pagination
- POST /notes: create a new note for the current user
- GET /notes/<id>: fetch one note for the current user
- PATCH /notes/<id>: update one note for the current user
- DELETE /notes/<id>: delete one note for the current user
