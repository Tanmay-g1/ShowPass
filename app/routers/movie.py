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