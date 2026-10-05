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