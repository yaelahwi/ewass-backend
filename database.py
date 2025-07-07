from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager

import os
from dotenv import load_dotenv

load_dotenv()

# Use SQLite instead of PostgreSQL
# DATABASE_URL = "sqlite:///./bpr.db"
# DATABASE_URL = "postgresql://postgres:Khoi2000@localhost:5432/bpr_db"


# Akses variabel menggunakan os.getenv()
DATABASE_URL= os.getenv("DATABASE_URL")


try:
    # Create database engine
    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv('SQL_ECHO', 'False').lower() == 'true'  # SQL logging
    )
    
    # Test database connection
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        print("Database connection successful")
        
except Exception as e:
    print(f"Database connection error: {str(e)}")
    raise

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()

@contextmanager
def get_db():
    """
    Get database session with error handling
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        print(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

