"""Pydantic schemas for API request/response validation."""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


# ============================================================================
# Request Schemas
# ============================================================================

class CreateSessionRequest(BaseModel):
    """Request to create new interview session."""
    resume_text: str = Field(..., min_length=50, max_length=500000, description="Candidate's resume")
    job_description_text: str = Field(..., min_length=50, max_length=100000, description="Job description")

    @validator('resume_text', 'job_description_text')
    def validate_not_empty(cls, v):
        """Validate text is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError("Text cannot be empty or whitespace only")
        return v.strip()


class SubmitResponseRequest(BaseModel):
    """Request to submit candidate response."""
    response: str = Field(..., max_length=50000, description="Candidate's answer")


class UpdateSessionStatusRequest(BaseModel):
    """Request to update session status."""
    status: str = Field(..., pattern="^(active|paused|completed)$")


# ============================================================================
# Response Schemas
# ============================================================================

class TopicSchema(BaseModel):
    """Topic schema."""
    name: str
    priority: int
    depth: str
    questions_asked: int
    covered: bool

    class Config:
        from_attributes = True


class MessageSchema(BaseModel):
    """Message schema."""
    id: UUID
    role: str
    content: str
    topic: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}

    class Config:
        from_attributes = True


class EvaluationSchema(BaseModel):
    """Evaluation schema."""
    id: UUID
    question: str
    response: str
    topic: str
    technical_accuracy: float
    depth: float
    clarity: float
    relevance: float
    overall_score: float
    strengths: List[str]
    gaps: List[str]
    feedback: str
    timestamp: datetime

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    """Session response schema."""
    id: UUID
    candidate_name: str
    job_title: str
    company: str
    current_topic: str
    current_topic_index: int
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    questions_asked: int
    average_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class SessionDetailResponse(SessionResponse):
    """Detailed session response with messages and evaluations."""
    candidate_profile: Dict[str, Any]
    job_requirements: Dict[str, Any]
    topics: List[Dict[str, Any]]
    messages: List[MessageSchema]
    evaluations: List[EvaluationSchema]


class QuestionResponse(BaseModel):
    """Response containing generated question."""
    question: str
    topic: str
    question_number: int
    topic_progress: str  # e.g., "2/5"
    questions_in_topic: int


class EvaluationResponse(BaseModel):
    """Response after evaluating answer."""
    evaluation: EvaluationSchema
    next_question: Optional[QuestionResponse]
    transitioned: bool
    transition_reasoning: Optional[str]
    interview_complete: bool


class FinalReportResponse(BaseModel):
    """Final interview report response."""
    id: UUID
    session_id: UUID
    candidate_name: str
    job_title: str
    duration_minutes: float
    total_questions: int
    topics_covered: List[str]
    overall_score: float
    topic_summaries: List[Dict[str, Any]]
    overall_strengths: List[str]
    areas_for_improvement: List[str]
    recommendation: str
    additional_notes: Optional[str]

    class Config:
        from_attributes = True


# ============================================================================
# WebSocket Schemas
# ============================================================================

class WSMessage(BaseModel):
    """WebSocket message schema."""
    type: str  # "question" | "response" | "evaluation" | "status" | "error" | "complete"
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WSQuestionMessage(BaseModel):
    """WebSocket question message."""
    type: str = "question"
    question: str
    topic: str
    question_number: int
    expected_elements: List[str]


class WSEvaluationMessage(BaseModel):
    """WebSocket evaluation message."""
    type: str = "evaluation"
    scores: Dict[str, float]
    overall_score: float
    strengths: List[str]
    gaps: List[str]
    feedback: str


class WSStatusMessage(BaseModel):
    """WebSocket status update."""
    type: str = "status"
    current_topic: str
    topic_index: int
    total_topics: int
    questions_asked: int
    average_score: Optional[float]


class WSErrorMessage(BaseModel):
    """WebSocket error message."""
    type: str = "error"
    error: str
    recoverable: bool


# ============================================================================
# Health Check Schema
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    database: str
    circuit_breaker: Dict[str, str]
    timestamp: datetime
