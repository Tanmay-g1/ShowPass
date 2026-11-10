from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user  # <-- ADD THIS IMPORT

router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"]
)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.BookingResponse)
def create_booking(
    booking: schemas.BookingCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)  # <-- THE BOUNCER IS ACTIVE
):
    
    # 1. THE NEW PADLOCK (This should already be in your code from earlier)
    locked_seats = db.query(models.Seat).filter(
        models.Seat.id.in_(booking.seat_ids)
    ).with_for_update().all()

    # 2. THE CHECK
    existing_bookings = db.query(models.BookingSeat).join(models.Booking).filter(
        models.Booking.show_id == booking.show_id,
        models.BookingSeat.seat_id.in_(booking.seat_ids),
        models.Booking.status == "CONFIRMED"
    ).first()
    
    if existing_bookings:
        raise HTTPException(status_code=400, detail="One or more selected seats are already booked.")

    # 3. Create the main Booking record safely
    new_booking = models.Booking(
        user_id=current_user.id,  # <-- HIGHLY SECURE: ID pulled directly from the decrypted token
        show_id=booking.show_id,
        status="CONFIRMED"
    )
    db.add(new_booking)
    db.flush() 

    # 4. Link the specific seats
    for seat_id in booking.seat_ids:
        new_booking_seat = models.BookingSeat(
            booking_id=new_booking.id,
            seat_id=seat_id
        )
        db.add(new_booking_seat)

    # 5. COMMIT THE TRANSACTION
    db.commit()
    db.refresh(new_booking)
    
    return new_booking

@router.get("/", response_model=List[schemas.BookingResponse])
def get_my_bookings(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    # Fetch only the bookings where the user_id matches our decrypted token
    bookings = db.query(models.Booking).filter(
        models.Booking.user_id == current_user.id
    ).all()
    
    return bookings