# ShowPass - Project Understanding

Generated on 2026-11-10 from the files currently present in the project.

## 1. Project summary

ShowPass is the beginning of a movie-ticket booking backend. It is built with:

- FastAPI for HTTP API routes.
- SQLAlchemy for database models and database access.
- PostgreSQL as the intended database, configured through `DATABASE_URL`.
- Pydantic models for request validation and response serialization.
- Passlib with bcrypt for hashing signup passwords.

The current implementation is backend-only. The `frontend` directory exists but has no files in it yet.

The implemented backend currently supports:

1. A root health/welcome endpoint.
2. User signup with duplicate-email checking and bcrypt password hashing.
3. Movie creation and movie listing.
4. Cinema screen creation, including automatic seat generation.
5. Show creation after validating the referenced movie and screen.
6. Booking creation for one or more seat IDs, with a check for already-confirmed seats.

The application creates all SQLAlchemy tables at startup using `Base.metadata.create_all()`. There are no database migrations yet.

## 2. Current project structure

```text
ShowPass/
├── UNDERSTANDME.md                 This project handoff document
├── backend/
│   ├── .env                        Local database configuration (secret value redacted below)
│   ├── .gitignore
│   └── app/
│       ├── database.py             SQLAlchemy engine, session factory, and DB dependency
│       ├── main.py                 FastAPI application and router registration
│       ├── models.py                SQLAlchemy database tables and relationships
│       ├── schemas.py               Pydantic request/response schemas
│       └── routers/
│           ├── booking.py           Booking creation
│           ├── cinema.py            Screen and show creation
│           ├── movie.py             Movie creation and listing
│           └── user.py              User signup
└── frontend/                       Currently empty
```

The local `backend/venv/` directory also contains installed Python packages and generated environment files. It is an environment artifact, not application source, and is excluded from this document.

## 3. API endpoints currently implemented

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Returns a welcome/health message |
| POST | `/users/` | Creates a user after hashing the password |
| POST | `/movies/` | Creates a movie |
| GET | `/movies/` | Returns all movies |
| POST | `/cinema/screens` | Creates a screen and generates its seats |
| POST | `/cinema/shows` | Creates a show after checking movie and screen IDs |
| POST | `/bookings/` | Creates a confirmed booking for selected seats |

FastAPI should also expose interactive API documentation at `/docs` and `/redoc` when the server is running.

## 4. Data model

The database model has these tables:

- `users`: email and hashed password.
- `movies`: movie title and duration.
- `screens`: cinema screen name and total capacity.
- `seats`: individual seats attached to a screen.
- `shows`: a movie scheduled on a screen at a start time.
- `bookings`: a user's booking for a show, with a status and creation time.
- `booking_seats`: links bookings to their selected seats.

Relationships currently connect:

- A user to their bookings.
- A movie to its shows.
- A screen to its shows and seats.
- A show to its movie, screen, and bookings.
- A booking to its user, show, and booking-seat records.
- A booking-seat record to its booking and seat.

## 5. What has been done

### Application startup

- The FastAPI app is named `ShowPass API`.
- The app description identifies it as the backend for a movie booking system.
- SQLAlchemy tables are created when `app.main` is imported.
- User, movie, cinema, and booking routers are included.

### Users

- Signup accepts an email and password.
- Existing emails are rejected with HTTP 400.
- Passwords are hashed with bcrypt before being stored.
- The response only exposes the user ID and email, not the password hash.

### Movies

- Movies can be created with a title and duration in minutes.
- All movies can be listed.

### Cinema screens and seats

- A screen accepts a name, row count, and seats-per-row count.
- Capacity is calculated as `num_rows * seats_per_row`.
- Individual seats are generated using row letters and numeric seat positions.
- Rows after 26 reuse letters because the current implementation uses `row % 26`.

### Shows

- A show references a movie, screen, and start time.
- The movie and screen are checked before the show is inserted.
- Missing references return HTTP 404.

### Bookings

- A booking accepts a user ID, show ID, and a list of seat IDs.
- Existing confirmed bookings are checked for seat conflicts.
- A new booking is created with `CONFIRMED` status.
- Booking-seat links are added and committed in the same request flow.
- A row-locking query (`with_for_update`) is present for the conflict check.

## 6. Important current limitations and next work

These are not implemented yet in the current files:

- No frontend.
- No login endpoint or authentication/session/JWT mechanism.
- No authorization or admin protection for creating movies, screens, shows, or bookings.
- Booking input does not verify that the user exists.
- Booking input does not verify that the show exists.
- Booking input does not verify that each seat exists or belongs to the screen used by the show.
- There are no explicit database uniqueness constraints preventing duplicate booking-seat links.
- The booking transaction does not explicitly roll back if a later database operation fails.
- There is no booking cancellation endpoint.
- There is no endpoint for listing screens, seats, shows, available seats, or bookings.
- There is no validation for positive row counts, seat counts, movie duration, or other domain limits.
- Screen creation commits the screen before generating seats, so seat-generation failure could leave a partially created screen.
- The screen row naming scheme repeats letters after 26 rows.
- `create_all()` is used instead of Alembic or another migration system.
- No automated tests are present.
- No dependency manifest such as `requirements.txt` or `pyproject.toml` is present.
- No deployment configuration, CORS configuration, logging setup, or environment validation is present.
- No documentation explains the startup command or database setup.

## 7. Suggested order for resuming work

1. Add a dependency manifest and a clear local startup README.
2. Add database migrations, preferably Alembic.
3. Add database constraints and input validation for users, shows, seats, and bookings.
4. Add authentication and authorization before exposing admin-style creation endpoints.
5. Add endpoints for browsing cinemas, shows, seats, and bookings.
6. Add automated API and database tests, especially concurrent seat-booking tests.
7. Build the frontend and connect it to the API.
8. Add CORS and deployment configuration once the client/server architecture is decided.

## 8. File-by-file contents

The source files are reproduced below as they currently exist.

### `backend/app/main.py`

```python
from fastapi import FastAPI
from . import models
from .database import engine
from .routers import user,movie,cinema,booking

# This line tells SQLAlchemy to look at models.py and create the tables in PostgreSQL
models.Base.metadata.create_all(bind=engine)

# Initialize the FastAPI app
app = FastAPI(
    title="ShowPass API",
    description="Backend for the ShowPass movie booking system",
    version="1.0.0"
)

# THIS IS THE MISSING LINE: Plug the router into the main app
app.include_router(user.router)
app.include_router(movie.router)
app.include_router(cinema.router)
app.include_router(booking.router)

# Let's keep the welcome message too so the root URL still works
@app.get("/")
def read_root():
    return {"message": "Welcome to the ShowPass API! The server is running."}
```

### `backend/app/database.py`

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load the variables from the .env file
load_dotenv()

# Get the database URL
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Create the engine that manages the connection to the database
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a session factory (used to talk to the DB in our endpoints)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that all our future database models will inherit from
Base = declarative_base()

# Dependency to get a database session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### `backend/app/models.py`

```python
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    
    # Relationships help us fetch all bookings for a user easily
    bookings = relationship("Booking", back_populates="user")

class Movie(Base):
    __tablename__ = "movies"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    duration_minutes = Column(Integer)
    
    shows = relationship("Show", back_populates="movie")

class Screen(Base):
    __tablename__ = "screens"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    total_capacity = Column(Integer)
    
    shows = relationship("Show", back_populates="screen")
    seats = relationship("Seat", back_populates="screen")

class Show(Base):
    __tablename__ = "shows"
    
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"))
    screen_id = Column(Integer, ForeignKey("screens.id"))
    start_time = Column(DateTime)
    
    movie = relationship("Movie", back_populates="shows")
    screen = relationship("Screen", back_populates="shows")
    bookings = relationship("Booking", back_populates="show")

class Seat(Base):
    __tablename__ = "seats"
    
    id = Column(Integer, primary_key=True, index=True)
    screen_id = Column(Integer, ForeignKey("screens.id"))
    row_letter = Column(String)
    seat_number = Column(Integer)
    
    screen = relationship("Screen", back_populates="seats")

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    show_id = Column(Integer, ForeignKey("shows.id"))
    status = Column(String, default="PENDING") # PENDING, CONFIRMED, or CANCELLED
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="bookings")
    show = relationship("Show", back_populates="bookings")
    seats = relationship("BookingSeat", back_populates="booking")

class BookingSeat(Base):
    __tablename__ = "booking_seats"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"))
    seat_id = Column(Integer, ForeignKey("seats.id"))
    
    booking = relationship("Booking", back_populates="seats")
    seat = relationship("Seat")
```

### `backend/app/schemas.py`

```python
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# --- USER SCHEMAS ---

# What the user sends us when they sign up
class UserCreate(BaseModel):
    email: str
    password: str

# What we send back to the user (Notice we DO NOT send the password back!)
class UserResponse(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True  # Tells Pydantic to read data from SQLAlchemy models

# --- MOVIE SCHEMAS ---

# What the admin sends us to add a movie
class MovieCreate(BaseModel):
    title: str
    duration_minutes: int

# What we send back to the frontend when it asks for the movie list
class MovieResponse(BaseModel):
    id: int
    title: str
    duration_minutes: int

    class Config:
        from_attributes = True

# --- CINEMA SCHEMAS ---

# Notice we ask for rows and seats, not the total capacity!
class ScreenCreate(BaseModel):
    name: str
    num_rows: int
    seats_per_row: int

class ScreenResponse(BaseModel):
    id: int
    name: str
    total_capacity: int

    class Config:
        from_attributes = True

class ShowCreate(BaseModel):
    movie_id: int
    screen_id: int
    start_time: datetime

class ShowResponse(BaseModel):
    id: int
    movie_id: int
    screen_id: int
    start_time: datetime

    class Config:
        from_attributes = True  

# --- BOOKING SCHEMAS ---

class BookingCreate(BaseModel):
    user_id: int
    show_id: int
    seat_ids: List[int]  # Accepts a list of multiple seat IDs

class BookingResponse(BaseModel):
    id: int
    user_id: int
    show_id: int
    status: str
    
    class Config:
        from_attributes = True
```

### `backend/app/routers/user.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from .. import models, schemas
from ..database import get_db

# This acts like a mini-FastAPI app just for user-related routes
router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

# Set up the password hashing engine
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)

# The actual signup endpoint
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    
    # 1. Check if the email is already in the database
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # 2. Hash the password
    hashed_password = get_password_hash(user.password)
    
    # 3. Create the SQLAlchemy model instance
    new_user = models.User(email=user.email, password_hash=hashed_password)
    
    # 4. Save it to PostgreSQL
    db.add(new_user)
    db.commit()
    db.refresh(new_user) # Refreshes to get the new ID generated by PostgreSQL
    
    return new_user
```

### `backend/app/routers/movie.py`

```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/movies",
    tags=["Movies"]
)

# Endpoint to add a new movie to the database
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.MovieResponse)
def create_movie(movie: schemas.MovieCreate, db: Session = Depends(get_db)):
    new_movie = models.Movie(title=movie.title, duration_minutes=movie.duration_minutes)
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)
    return new_movie

# Endpoint to fetch ALL movies to display on the frontend
@router.get("/", response_model=List[schemas.MovieResponse])
def get_movies(db: Session = Depends(get_db)):
    movies = db.query(models.Movie).all()
    return movies
```

### `backend/app/routers/cinema.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/cinema",
    tags=["Cinema"]
)

@router.post("/screens", status_code=status.HTTP_201_CREATED, response_model=schemas.ScreenResponse)
def create_screen(screen: schemas.ScreenCreate, db: Session = Depends(get_db)):
    # 1. Calculate the total capacity dynamically
    total_capacity = screen.num_rows * screen.seats_per_row
    
    # 2. Save the Screen to the database
    new_screen = models.Screen(name=screen.name, total_capacity=total_capacity)
    db.add(new_screen)
    db.commit()
    db.refresh(new_screen)
    
    # 3. Auto-generate the individual Seats (A1, A2, B1, etc.)
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for row in range(screen.num_rows):
        row_letter = alphabet[row % 26] # Ensures we don't break if there are >26 rows
        for seat_num in range(1, screen.seats_per_row + 1):
            new_seat = models.Seat(
                screen_id=new_screen.id,
                row_letter=row_letter,
                seat_number=seat_num
            )
            db.add(new_seat)
            
    # 4. Commit all the newly generated seats to the database at once
    db.commit() 
    
    return new_screen

@router.post("/shows", status_code=status.HTTP_201_CREATED, response_model=schemas.ShowResponse)
def create_show(show: schemas.ShowCreate, db: Session = Depends(get_db)):
    # Verify the movie actually exists before scheduling
    movie = db.query(models.Movie).filter(models.Movie.id == show.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
        
    # Verify the screen actually exists
    screen = db.query(models.Screen).filter(models.Screen.id == show.screen_id).first()
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
        
    # **show.model_dump() unpacks the dictionary (movie_id, screen_id, start_time) instantly
    new_show = models.Show(**show.model_dump())
    db.add(new_show)
    db.commit()
    db.refresh(new_show)
    return new_show
```

### `backend/app/routers/booking.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"]
)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.BookingResponse)
def create_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db)):
    
    # 1. CONCURRENCY CHECK: Are any of these seats already taken for this show?
    existing_bookings = db.query(models.BookingSeat).join(models.Booking).filter(
        models.Booking.show_id == booking.show_id,
        models.BookingSeat.seat_id.in_(booking.seat_ids),
        models.Booking.status == "CONFIRMED"
    ).with_for_update().first()
    
    if existing_bookings:
        raise HTTPException(status_code=400, detail="One or more selected seats are already booked.")

    # 2. Create the main Booking record
    new_booking = models.Booking(
        user_id=booking.user_id,
        show_id=booking.show_id,
        status="CONFIRMED"
    )
    db.add(new_booking)
    
    # flush() sends the booking to the database to get an ID, but DOES NOT save it permanently yet.
    # This is the start of our safety transaction.
    db.flush() 

    # 3. Link the specific seats to this newly created booking
    for seat_id in booking.seat_ids:
        new_booking_seat = models.BookingSeat(
            booking_id=new_booking.id,
            seat_id=seat_id
        )
        db.add(new_booking_seat)

    # 4. COMMIT THE TRANSACTION
    # If anything failed above, none of this saves. If it all worked, it saves together.
    db.commit()
    db.refresh(new_booking)
    
    return new_booking
```

### `backend/.gitignore`

```text
venv/
__pycache__/
.env
*.pyc
```

### `backend/.env`

This file exists and contains one local environment variable:

```text
DATABASE_URL=***REDACTED***
```

The actual database URL is intentionally not copied into this handoff document. Keep `.env` local and do not commit its credential.

### `frontend/`

This directory is currently empty. No frontend source, package manifest, configuration, or assets have been created yet.
