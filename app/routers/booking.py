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