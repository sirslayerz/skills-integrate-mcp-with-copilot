"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import json
import os
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


def load_teachers():
    """Load teacher credentials from the JSON file."""
    teacher_file = Path(__file__).parent / "teachers.json"
    if not teacher_file.exists():
        return {}

    with teacher_file.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, dict):
        if isinstance(data.get("teachers"), list):
            data = data["teachers"]
        else:
            return data

    if isinstance(data, list):
        return {
            teacher["username"]: teacher["password"]
            for teacher in data
            if isinstance(teacher, dict)
            and "username" in teacher
            and "password" in teacher
        }

    return {}


teachers = load_teachers()


def is_authenticated(username: str | None, password: str | None) -> bool:
    return bool(username and password and teachers.get(username) == password)


def extract_credentials(request: Request, username: str | None, password: str | None):
    if username or password:
        return username, password

    authorization = request.headers.get("authorization", "")
    if authorization.startswith("Basic "):
        import base64

        try:
            decoded = base64.b64decode(authorization.removeprefix("Basic ")).decode("utf-8")
            basic_username, basic_password = decoded.split(":", 1)
            return basic_username, basic_password
        except (ValueError, UnicodeDecodeError):
            return None, None

    return None, None


def require_teacher(request: Request, username: str | None, password: str | None):
    username, password = extract_credentials(request, username, password)
    if not is_authenticated(username, password):
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/login")
async def login(request: Request):
    username = request.query_params.get("username")
    password = request.query_params.get("password")

    try:
        body = await request.json()
    except Exception:
        body = {}

    if isinstance(body, dict):
        username = body.get("username", username)
        password = body.get("password", password)

    if not is_authenticated(username, password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {"message": "Logged in successfully", "username": username}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    request: Request,
    email: str,
    username: str | None = None,
    password: str | None = None,
    teacher_username: str | None = None,
    teacher_password: str | None = None,
):
    """Sign up a student for an activity"""
    username = username or teacher_username
    password = password or teacher_password
    require_teacher(request, username, password)

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    request: Request,
    email: str,
    username: str | None = None,
    password: str | None = None,
    teacher_username: str | None = None,
    teacher_password: str | None = None,
):
    """Unregister a student from an activity"""
    username = username or teacher_username
    password = password or teacher_password
    require_teacher(request, username, password)

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
