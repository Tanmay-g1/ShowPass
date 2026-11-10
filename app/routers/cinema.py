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