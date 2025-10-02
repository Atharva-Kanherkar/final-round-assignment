"""SQLAlchemy database models."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from api.database import Base


class SessionStatus(str, enum.Enum):
    """Session status enumeration."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class DBSession(Base):
    """Database model for interview session."""
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_name = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)

    # JSON fields for complex data
    candidate_profile = Column(JSON, nullable=False)
    job_requirements = Column(JSON, nullable=False)
    topics = Column(JSON, nullable=False)

    # Session state
    current_topic = Column(String(100), nullable=False)
    current_topic_index = Column(Integer, default=0)
    status = Column(String(20), default="active", nullable=False)  # Using String instead of Enum to avoid migration issues

    # Timestamps
    start_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)

    # Metrics
    questions_asked = Column(Integer, default=0)
    average_score = Column(Float, nullable=True)

    # Relationships
    messages = relationship("DBMessage", back_populates="session", cascade="all, delete-orphan")
    evaluations = relationship("DBEvaluation", back_populates="session", cascade="all, delete-orphan")

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class DBMessage(Base):
    """Database model for conversation messages."""
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)

    role = Column(String(50), nullable=False)  # "interviewer" | "candidate"
    content = Column(Text, nullable=False)
    topic = Column(String(100), nullable=False)
    msg_metadata = Column(JSON, default=dict)  # Renamed to avoid SQLAlchemy reserved word

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    session = relationship("DBSession", back_populates="messages")


class DBEvaluation(Base):
    """Database model for response evaluations."""
    __tablename__ = "evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)

    question = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    topic = Column(String(100), nullable=False)

    # Scores
    technical_accuracy = Column(Float, nullable=False)
    depth = Column(Float, nullable=False)
    clarity = Column(Float, nullable=False)
    relevance = Column(Float, nullable=False)
    overall_score = Column(Float, nullable=False)

    # Feedback
    strengths = Column(JSON, default=list)
    gaps = Column(JSON, default=list)
    feedback = Column(Text, nullable=False)

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    session = relationship("DBSession", back_populates="evaluations")


class DBFinalReport(Base):
    """Database model for final interview report."""
    __tablename__ = "final_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), unique=True, nullable=False)

    candidate_name = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False)
    duration_minutes = Column(Float, nullable=False)

    total_questions = Column(Integer, nullable=False)
    topics_covered = Column(JSON, nullable=False)
    overall_score = Column(Float, nullable=False)

    # Report details
    topic_summaries = Column(JSON, nullable=False)
    overall_strengths = Column(JSON, default=list)
    areas_for_improvement = Column(JSON, default=list)
    recommendation = Column(String(50), nullable=False)
    additional_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
