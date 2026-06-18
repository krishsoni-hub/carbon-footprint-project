from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Instantiate SQLAlchemy database instance to bind with Flask app context
db = SQLAlchemy()

class User(db.Model):
    """Data model representing a registered system user."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    logs = db.relationship('CarbonLog', backref='user', lazy=True, cascade="all, delete-orphan")
    goals = db.relationship('UserGoal', backref='user', lazy=True, cascade="all, delete-orphan")

    def __init__(self, id=None, username=None, date_created=None):
        if id is not None:
            self.id = id
        if username is not None:
            self.username = username
        if date_created is not None:
            self.date_created = date_created

    def to_dict(self):
        """Serialize User model properties into dict mapping."""
        return {
            "id": self.id,
            "username": self.username,
            "date_created": self.date_created.isoformat() if self.date_created else None
        }


class CarbonLog(db.Model):
    """Data model representing a detailed logged carbon footprint entry for a user."""
    __tablename__ = 'carbon_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True, nullable=False)
    transport_emissions = db.Column(db.Float, nullable=False)
    energy_emissions = db.Column(db.Float, nullable=False)
    diet_emissions = db.Column(db.Float, nullable=False)
    total_emissions = db.Column(db.Float, nullable=False)
    source_text = db.Column(db.Text, nullable=True)

    def __init__(self, user_id, transport_emissions, energy_emissions, diet_emissions, total_emissions, source_text=None, timestamp=None, id=None):
        if id is not None:
            self.id = id
        self.user_id = user_id
        self.transport_emissions = transport_emissions
        self.energy_emissions = energy_emissions
        self.diet_emissions = diet_emissions
        self.total_emissions = total_emissions
        if source_text is not None:
            self.source_text = source_text
        if timestamp is not None:
            self.timestamp = timestamp

    def to_dict(self):
        """Serialize CarbonLog model properties into dict mapping."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "transport_emissions": self.transport_emissions,
            "energy_emissions": self.energy_emissions,
            "diet_emissions": self.diet_emissions,
            "total_emissions": self.total_emissions,
            "source_text": self.source_text
        }


class UserGoal(db.Model):
    """Data model representing carbon emissions reduction goals set by a user."""
    __tablename__ = 'user_goals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    weekly_target = db.Column(db.Float, nullable=False)
    current_progress = db.Column(db.Float, default=0.0, nullable=False)
    status = db.Column(db.String(50), default="active", nullable=False)

    def __init__(self, user_id, weekly_target, current_progress=0.0, status="active", id=None):
        if id is not None:
            self.id = id
        self.user_id = user_id
        self.weekly_target = weekly_target
        self.current_progress = current_progress
        self.status = status

    def to_dict(self):
        """Serialize UserGoal model properties into dict mapping."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "weekly_target": self.weekly_target,
            "current_progress": self.current_progress,
            "status": self.status
        }


class CarbonMetric(db.Model):
    """Data model storing generalized carbon logs per category for dashboard metric states."""
    __tablename__ = 'carbon_metrics'

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(10), default="kg")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, category, value, unit="kg", updated_at=None, id=None):
        if id is not None:
            self.id = id
        self.category = category
        self.value = value
        self.unit = unit
        if updated_at is not None:
            self.updated_at = updated_at

    def to_dict(self):
        """Serialize CarbonMetric model properties into dict mapping."""
        return {
            "id": self.id,
            "category": self.category,
            "value": self.value,
            "unit": self.unit,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
