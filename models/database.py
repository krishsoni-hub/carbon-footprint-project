"""Database schema models for the Carbon Footprint application.

This module defines the User, CarbonLog, UserGoal, and CarbonMetric tables
using SQLAlchemy models, implementing secure password hashing using Werkzeug
and proper serialization functions.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Instantiate SQLAlchemy database instance to bind with Flask app context
db = SQLAlchemy()


class User(db.Model):  # type: ignore
    """Data model representing a registered system user."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    logs = db.relationship('CarbonLog', backref='user', lazy=True, cascade="all, delete-orphan")
    goals = db.relationship('UserGoal', backref='user', lazy=True, cascade="all, delete-orphan")

    def __init__(
        self,
        id: Optional[int] = None,
        username: Optional[str] = None,
        password_hash: Optional[str] = None,
        date_created: Optional[datetime] = None,
    ) -> None:
        """Initializes a User instance with optional credentials.

        Args:
            id (Optional[int]): Database primary key.
            username (Optional[str]): Unique display name.
            password_hash (Optional[str]): Hashed password string.
            date_created (Optional[datetime]): Timestamp of account creation.
        """
        if id is not None:
            self.id = id
        if username is not None:
            self.username = username
        if password_hash is not None:
            self.password_hash = password_hash
        if date_created is not None:
            self.date_created = date_created

    def set_password(self, password: str) -> None:
        """Hashes and secures the user's password.

        Args:
            password (str): The plain-text password to hash.

        Returns:
            None
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifies a plain-text password against the user's saved hash.

        Args:
            password (str): Plain-text password to test.

        Returns:
            bool: True if the password is correct, False otherwise.
        """
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize User model properties into dict mapping.

        Returns:
            Dict[str, Any]: Dictionary representation of the User instance.
        """
        return {
            "id": self.id,
            "username": self.username,
            "date_created": self.date_created.isoformat() if self.date_created else None
        }


class CarbonLog(db.Model):  # type: ignore
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

    def __init__(
        self,
        user_id: int,
        transport_emissions: float,
        energy_emissions: float,
        diet_emissions: float,
        total_emissions: float,
        source_text: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        id: Optional[int] = None,
    ) -> None:
        """Initializes a carbon log entry.

        Args:
            user_id (int): Foreign key identifier of the user.
            transport_emissions (float): Stored transport emissions.
            energy_emissions (float): Stored energy emissions.
            diet_emissions (float): Stored diet emissions.
            total_emissions (float): Stored sum total emissions.
            source_text (Optional[str]): Source chat instruction logged.
            timestamp (Optional[datetime]): Timestamp of the entry.
            id (Optional[int]): Database primary key.
        """
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

    def to_dict(self) -> Dict[str, Any]:
        """Serialize CarbonLog model properties into dict mapping.

        Returns:
            Dict[str, Any]: Dictionary representation of the CarbonLog instance.
        """
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


class UserGoal(db.Model):  # type: ignore
    """Data model representing carbon emissions reduction goals set by a user."""

    __tablename__ = 'user_goals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    weekly_target = db.Column(db.Float, nullable=False)
    current_progress = db.Column(db.Float, default=0.0, nullable=False)
    status = db.Column(db.String(50), default="active", nullable=False)

    def __init__(
        self,
        user_id: int,
        weekly_target: float,
        current_progress: float = 0.0,
        status: str = "active",
        id: Optional[int] = None,
    ) -> None:
        """Initializes user weekly goal limits.

        Args:
            user_id (int): Foreign key identifier of the user.
            weekly_target (float): Carbon target boundary.
            current_progress (float): Current emission log summation.
            status (str): Current status code (e.g. 'active', 'completed').
            id (Optional[int]): Database primary key.
        """
        if id is not None:
            self.id = id
        self.user_id = user_id
        self.weekly_target = weekly_target
        self.current_progress = current_progress
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        """Serialize UserGoal model properties into dict mapping.

        Returns:
            Dict[str, Any]: Dictionary representation of the UserGoal instance.
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "weekly_target": self.weekly_target,
            "current_progress": self.current_progress,
            "status": self.status
        }


class CarbonMetric(db.Model):  # type: ignore
    """Data model storing generalized carbon logs per category for dashboard metric states."""

    __tablename__ = 'carbon_metrics'

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(10), default="kg")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(
        self,
        category: str,
        value: float,
        unit: str = "kg",
        updated_at: Optional[datetime] = None,
        id: Optional[int] = None,
    ) -> None:
        """Initializes a CarbonMetric category state object.

        Args:
            category (str): Dynamic name of metric category.
            value (float): Numerical emissions rating.
            unit (str): Unit configuration.
            updated_at (Optional[datetime]): Timestamp of updates.
            id (Optional[int]): Database primary key.
        """
        if id is not None:
            self.id = id
        self.category = category
        self.value = value
        self.unit = unit
        if updated_at is not None:
            self.updated_at = updated_at

    def to_dict(self) -> Dict[str, Any]:
        """Serialize CarbonMetric model properties into dict mapping.

        Returns:
            Dict[str, Any]: Dictionary representation of the CarbonMetric instance.
        """
        return {
            "id": self.id,
            "category": self.category,
            "value": self.value,
            "unit": self.unit,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
