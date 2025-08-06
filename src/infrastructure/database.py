# src/infrastructure/database.py
"""Database configuration and initialization."""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.infrastructure.models import Base, GuestModel, RoomModel, BookingModel, HotelModel
from src.domain.value_objects import RoomNumber, RoomType, GuestCapacity

# Database URL - using SQLite for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hotel_booking.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize the database with tables and sample data."""
    print("Initializing database...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Add sample data if tables are empty
    db = SessionLocal()
    try:
        # Check if we already have data
        if db.query(RoomModel).count() > 0:
            print("Database already initialized with data.")
            return
        
        print("Adding sample rooms...")
        _create_sample_rooms(db)
        
        print("Adding default hotel...")
        _create_default_hotel(db)
        
        db.commit()
        print("Database initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def _create_sample_rooms(db: Session) -> None:
    """Create sample rooms for Crown Hotels."""
    rooms = []
    
    # Standard rooms (50) - floors 1-2
    for floor in range(1, 3):
        for room_num in range(1, 26):  # 25 rooms per floor
            room_number = f"{floor}{room_num:02d}"
            rooms.append(RoomModel(
                number=room_number,
                room_type=RoomType.STANDARD,
                max_capacity=2,
                is_available=True
            ))
    
    # Deluxe rooms (40) - floors 3-4
    for floor in range(3, 5):
        for room_num in range(1, 21):  # 20 rooms per floor
            room_number = f"{floor}{room_num:02d}"
            rooms.append(RoomModel(
                number=room_number,
                room_type=RoomType.DELUXE,
                max_capacity=3,
                is_available=True
            ))
    
    # Suite rooms (10) - floor 5
    for room_num in range(1, 11):
        room_number = f"5{room_num:02d}"
        rooms.append(RoomModel(
            number=room_number,
            room_type=RoomType.SUITE,
            max_capacity=4,
            is_available=True
        ))
    
    # Add all rooms to database
    db.add_all(rooms)
    print(f"Created {len(rooms)} rooms")


def _create_default_hotel(db: Session) -> None:
    """Create the default Crown Hotels entry."""
    hotel = HotelModel(
        name="Crown Hotels"
    )
    db.add(hotel)
    print("Created default hotel: Crown Hotels")


def reset_db() -> None:
    """Reset the database (drop all tables and recreate)."""
    print("Resetting database...")
    Base.metadata.drop_all(bind=engine)
    init_db()
    print("Database reset complete!")


if __name__ == "__main__":
    # Allow running this file directly to initialize the database
    init_db()
