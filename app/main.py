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