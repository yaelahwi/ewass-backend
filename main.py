import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from database import Base, engine
from utils.jwt_utils import blacklisted_tokens
from controller.bpr_scrapping import bpr_scrapping_bp
from controller.bpr_lainnya import bpr_lainnya_bp
from controller.rac import rac_bp
from controller.user import user_bp

# Load environment variables
load_dotenv()

# Create Flask application
app = Flask(__name__)

# JWT Configuration
app.config["JWT_SECRET_KEY"] = os.getenv('JWT_SECRET_KEY', 'your-super-secret-key')  # Change this in production!
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 24 * 60 * 60  # 24 hours
app.config["JWT_ERROR_MESSAGE_KEY"] = "message"
jwt = JWTManager(app)

from utils.jwt_utils import blacklisted_tokens

@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
    jti = jwt_payload["jti"]
    return jti in blacklisted_tokens

# JWT error handlers
@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        "status": "error",
        "message": "Invalid token format or signature"
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        "status": "error",
        "message": "Missing Authorization header. Format should be: Bearer <token>"
    }), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        "status": "error",
        "message": "Token has expired. Please login again"
    }), 401

@jwt.needs_fresh_token_loader
def token_not_fresh_callback():
    return jsonify({
        "status": "error",
        "message": "Fresh token required. Please login again"
    }), 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify({
        "status": "error",
        "message": "Token has been revoked"
    }), 401

# Create database tables
Base.metadata.create_all(bind=engine)

# Create asset directory if it doesn't exist
if not os.path.exists('asset'):
    os.makedirs('asset')

# Register blueprints
app.register_blueprint(bpr_scrapping_bp)
app.register_blueprint(bpr_lainnya_bp)
app.register_blueprint(rac_bp)
app.register_blueprint(user_bp)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return {'status': 'healthy', 'message': 'Service is running'}, 200

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.getenv('PORT', 5000))
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )
