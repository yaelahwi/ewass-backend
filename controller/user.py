from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    jwt_required,
    get_jwt_identity
)
from utils.jwt_utils import blacklisted_tokens
from database import get_db
from service.user_service import (
    create_user,
    get_all_users,
    get_user_by_id,
    verify_user,
    get_current_user
)

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        required_fields = ['uid','email', 'password', 'nama']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "status": "error",
                    "message": f"Missing required field: {field}"
                }), 400
                
        with get_db() as db:
            result = create_user(db, data)
            return jsonify(result), 201
            
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@user_bp.route('/login', methods=['POST'])
def login():
    """
    User login
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        uid = data.get('uid')
        password = data.get('password')
        
        if not uid or not password:
            return jsonify({
                "status": "error",
                "message": "UID and password are required"
            }), 400
            
        with get_db() as db:
            user = verify_user(db, uid, password)
            
            if user:
                # Generate access token with fresh=True for enhanced security
                access_token = create_access_token(
                    identity=str(user['uid']),
                    fresh=True
                )
                
                return jsonify({
                    "status": "success",
                    "message": "Login successful",
                    "access_token": access_token,
                    "token_type": "Bearer",
                    "user": user
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "message": "Invalid email or password"
                }), 401
            
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@user_bp.route('/', methods=['GET'])
def get_all():
    """
    Get all users
    """
    try:
        skip = request.args.get('skip', default=0, type=int)
        limit = request.args.get('limit', default=100, type=int)
        
        with get_db() as db:
            users = get_all_users(db, skip, limit)
            
            return jsonify({
                "status": "success",
                "data": users,
                "count": len(users)
            }), 200
            
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@user_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    User logout - blacklist the current token
    """
    try:
        jti = get_jwt()["jti"]
        blacklisted_tokens.add(jti)
        return jsonify({
            "status": "success",
            "message": "Successfully logged out"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Error during logout"
        }), 500

@user_bp.route('/<int:user_id>', methods=['GET'])
def get_detail(user_id: int):
    """
    Get user detail by ID
    """
    try:
        with get_db() as db:
            user = get_user_by_id(db, user_id)
            
            if not user:
                return jsonify({
                    "status": "error",
                    "message": f"User with ID {user_id} not found"
                }), 404
                
            return jsonify({
                "status": "success",
                "data": user
            }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    
@user_bp.route('/me', methods=['GET'])
@jwt_required()
def protected_route():
    with get_db() as db:
        user = get_current_user(db)
        
        if not user:
            return jsonify({"status": "error", "message": "Unauthorized"}), 401

        return jsonify({
            "status": "success",
            "name" : user.nama
        }), 200
