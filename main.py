from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime, timezone
import sqlite3
import logging
from typing import List, Optional
import pytz
from contextlib import asynccontextmanager, contextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    init_db()
    yield

app = FastAPI(title="Fitness Studio Booking API", version="1.0.0", lifespan=lifespan)

# Database setup
DATABASE_URL = "fitness_studio.db"

def init_db():
    """Initialize the database with tables and seed data"""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Create classes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            instructor TEXT NOT NULL,
            datetime TEXT NOT NULL,
            total_slots INTEGER NOT NULL,
            available_slots INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id INTEGER NOT NULL,
            client_name TEXT NOT NULL,
            client_email TEXT NOT NULL,
            booking_time TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (class_id) REFERENCES classes (id)
        )
    ''')
    
    # Insert seed data (classes in IST)
    ist = pytz.timezone('Asia/Kolkata')
    seed_classes = [
        ("Yoga Flow", "Priya Sharma", "2025-06-09 07:00:00", 20, 20),
        ("Zumba Dance", "Rahul Kumar", "2025-06-09 18:30:00", 25, 25),
        ("HIIT Training", "Anjali Singh", "2025-06-10 06:30:00", 15, 15),
        ("Power Yoga", "Priya Sharma", "2025-06-10 19:00:00", 20, 20),
        ("Cardio Blast", "Vikram Patel", "2025-06-11 07:30:00", 18, 18),
    ]
    
    for name, instructor, dt_str, total, available in seed_classes:
        # Convert to IST timezone aware datetime
        naive_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        ist_dt = ist.localize(naive_dt)
        
        cursor.execute('''
            INSERT OR IGNORE INTO classes (name, instructor, datetime, total_slots, available_slots)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, instructor, ist_dt.isoformat(), total, available))
    
    conn.commit()
    conn.close()
    logger.info("Database initialized with seed data")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@contextmanager
def get_db():
    """Database connection context manager"""
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Pydantic models
class ClassResponse(BaseModel):
    id: int
    name: str
    instructor: str
    datetime: str
    total_slots: int
    available_slots: int

class BookingRequest(BaseModel):
    class_id: int
    client_name: str
    client_email: EmailStr
    
    @field_validator('client_name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Client name cannot be empty')
        return v.strip()

class BookingResponse(BaseModel):
    id: int
    class_id: int
    class_name: str
    instructor: str
    class_datetime: str
    client_name: str
    client_email: str
    booking_time: str

def convert_timezone(dt_str: str, target_tz: str = "UTC") -> str:
    """Convert datetime from IST to target timezone"""
    try:
        # Parse the ISO format datetime
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        
        # If datetime is naive, assume it's in IST
        if dt.tzinfo is None:
            ist = pytz.timezone('Asia/Kolkata')
            dt = ist.localize(dt)
        
        # Convert to target timezone
        target_tz_obj = pytz.timezone(target_tz)
        converted_dt = dt.astimezone(target_tz_obj)
        
        return converted_dt.isoformat()
    except Exception as e:
        logger.error(f"Error converting timezone: {e}")
        return dt_str



@app.get("/")
async def read_root():
    """Health check endpoint"""
    return {"message": "Fitness Studio Booking API", "status": "running"}

@app.get("/classes", response_model=List[ClassResponse])
async def get_classes(timezone: str = Query("Asia/Kolkata", description="Timezone for class times")):
    """
    Get all upcoming fitness classes
    
    Args:
        timezone: Target timezone for class times (default: Asia/Kolkata)
    
    Returns:
        List of available classes with their details
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, instructor, datetime, total_slots, available_slots
                FROM classes
                WHERE datetime > ?
                ORDER BY datetime
            ''', (datetime.now(pytz.UTC).isoformat(),))
            
            classes = []
            for row in cursor.fetchall():
                class_data = dict(row)
                # Convert datetime to requested timezone
                class_data['datetime'] = convert_timezone(class_data['datetime'], timezone)
                classes.append(ClassResponse(**class_data))
            
            logger.info(f"Retrieved {len(classes)} classes")
            return classes
            
    except Exception as e:
        logger.error(f"Error fetching classes: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/book", response_model=dict)
async def book_class(booking: BookingRequest):
    """
    Book a spot in a fitness class
    
    Args:
        booking: Booking request with class_id, client_name, and client_email
    
    Returns:
        Booking confirmation details
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if class exists and has available slots
            cursor.execute('''
                SELECT id, name, instructor, datetime, available_slots
                FROM classes
                WHERE id = ? AND datetime > ?
            ''', (booking.class_id, datetime.now(pytz.UTC).isoformat()))
            
            class_info = cursor.fetchone()
            if not class_info:
                raise HTTPException(
                    status_code=404, 
                    detail="Class not found or has already occurred"
                )
            
            if class_info['available_slots'] <= 0:
                raise HTTPException(
                    status_code=400, 
                    detail="No available slots for this class"
                )
            
            # Check if user already booked this class
            cursor.execute('''
                SELECT id FROM bookings
                WHERE class_id = ? AND client_email = ?
            ''', (booking.class_id, booking.client_email))
            
            if cursor.fetchone():
                raise HTTPException(
                    status_code=400,
                    detail="You have already booked this class"
                )
            
            # Create booking
            cursor.execute('''
                INSERT INTO bookings (class_id, client_name, client_email, booking_time)
                VALUES (?, ?, ?, ?)
            ''', (booking.class_id, booking.client_name, booking.client_email, 
                  datetime.now(pytz.UTC).isoformat()))
            
            booking_id = cursor.lastrowid
            
            # Update available slots
            cursor.execute('''
                UPDATE classes
                SET available_slots = available_slots - 1
                WHERE id = ?
            ''', (booking.class_id,))
            
            conn.commit()
            
            logger.info(f"Booking created: {booking_id} for class {booking.class_id}")
            
            return {
                "message": "Booking successful",
                "booking_id": booking_id,
                "class_name": class_info['name'],
                "instructor": class_info['instructor'],
                "class_datetime": class_info['datetime'],
                "client_name": booking.client_name,
                "client_email": booking.client_email
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating booking: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/bookings", response_model=List[BookingResponse])
async def get_bookings(
    email: EmailStr = Query(..., description="Client email to fetch bookings for"),
    timezone: str = Query("Asia/Kolkata", description="Timezone for class times")
):
    """
    Get all bookings for a specific email address
    
    Args:
        email: Client email address
        timezone: Target timezone for class times (default: Asia/Kolkata)
    
    Returns:
        List of bookings for the specified email
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    b.id, b.class_id, b.client_name, b.client_email, b.booking_time,
                    c.name as class_name, c.instructor, c.datetime as class_datetime
                FROM bookings b
                JOIN classes c ON b.class_id = c.id
                WHERE b.client_email = ?
                ORDER BY c.datetime DESC
            ''', (email,))
            
            bookings = []
            for row in cursor.fetchall():
                booking_data = dict(row)
                # Convert class datetime to requested timezone
                booking_data['class_datetime'] = convert_timezone(
                    booking_data['class_datetime'], timezone
                )
                bookings.append(BookingResponse(**booking_data))
            
            logger.info(f"Retrieved {len(bookings)} bookings for {email}")
            return bookings
            
    except Exception as e:
        logger.error(f"Error fetching bookings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now(pytz.UTC).isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)