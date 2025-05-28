from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash
from object.models import User
from dto.user_schema import UserSchema, UserResponseSchema

def create_user(db: Session, user_data: Dict) -> Dict:
    """
    Create a new user
    
    Args:
        db (Session): Database session
        user_data (Dict): User data including email, password, and nama
        
    Returns:
        Dict: Created user data
        
    Raises:
        ValueError: If user creation fails
    """
    try:
        # Validate user data
        schema = UserSchema()
        validated_data = schema.load(user_data)
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == validated_data['email']).first()
        if existing_user:
            raise ValueError("Email already registered")
        
        # Hash password
        validated_data['password'] = generate_password_hash(validated_data['password'])
        
        # Create user
        user = User(**validated_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Return user data without password
        response_schema = UserResponseSchema()
        return {
            "status": "success",
            "uid": user.id,
            "user": response_schema.dump(user)
        }
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error creating user: {str(e)}")

def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[Dict]:
    """
    Get all users
    
    Args:
        db (Session): Database session
        skip (int): Number of records to skip
        limit (int): Maximum number of records to return
        
    Returns:
        List[Dict]: List of user data
    """
    users = db.query(User).offset(skip).limit(limit).all()
    schema = UserResponseSchema()
    return [schema.dump(user) for user in users]

def get_user_by_id(db: Session, user_id: int) -> Optional[Dict]:
    """
    Get user by ID
    
    Args:
        db (Session): Database session
        user_id (int): User ID
        
    Returns:
        Optional[Dict]: User data if found, None otherwise
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        schema = UserResponseSchema()
        return schema.dump(user)
    return None

def verify_user(db: Session, email: str, password: str) -> Optional[Dict]:
    """
    Verify user credentials
    
    Args:
        db (Session): Database session
        email (str): User email
        password (str): User password
        
    Returns:
        Optional[Dict]: User data if verification successful, None otherwise
    """
    user = db.query(User).filter(User.email == email).first()
    if user and check_password_hash(user.password, password):
        schema = UserResponseSchema()
        return schema.dump(user)
    return None
