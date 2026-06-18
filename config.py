import os
from dotenv import load_dotenv

# Load environmental configurations from local .env file
load_dotenv()

class Config:
    """Configuration class for Carbon Footprint Awareness Web Application."""
    # Security Key for Session management and flash messages
    SECRET_KEY = os.getenv("SECRET_KEY", "prod-ready-fallback-secret-key-309485720938")
    
    # API key for Google Gemini model Integration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///carbon_footprint.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
