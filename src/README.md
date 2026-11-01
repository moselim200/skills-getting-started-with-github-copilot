# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- See signed-up participants in a styled list without bullet points on each activity card
- Sign up for activities
- Unregister participants using the delete icon beside their email; participant counts and availability refresh automatically

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a participant (404 for an unknown activity, 400 if not signed up) |

## Testing

From the repository root, install dependencies and run the backend tests:

```bash
python -m pip install -r requirements.txt
python -m pytest
```

The pytest suite lives in `tests/` and uses FastAPI's in-process `TestClient`,
so no running server is needed. Shared fixtures restore the in-memory activity
data after every test, including failures.

Structure backend tests using Arrange-Act-Assert (AAA), separated by blank lines:

- **Arrange:** prepare inputs, fixture data, and expected results.
- **Act:** perform requests and capture responses, including subsequent activity listings.
- **Assert:** check response status, content, and state without performing requests.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
