"""Data models for interview session management."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from .candidate import CandidateProfile, JobRequirements, Topic
from .evaluation import ResponseEvaluation, FinalReport


class SessionStatus(Enum):
    """Interview session status."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class Message:
    """Represents a message in the conversation."""
    role: str  # "interviewer" | "candidate"
    content: str
    timestamp: datetime
    topic: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "topic": self.topic,
            "metadata": self.metadata
        }


@dataclass
class InterviewSession:
    """Represents an interview session with all state."""
    session_id: str
    candidate_profile: CandidateProfile
    job_requirements: JobRequirements
    topics: List[Topic]

    # Session state
    current_topic: str
    current_topic_index: int = 0
    status: SessionStatus = SessionStatus.ACTIVE
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    # Conversation
    conversation_history: List[Message] = field(default_factory=list)

    # Evaluations
    evaluations: List[ResponseEvaluation] = field(default_factory=list)
    final_report: Optional[FinalReport] = None

    # Metrics
    questions_asked: int = 0

    def add_message(self, role: str, content: str, topic: str, metadata: Dict[str, Any] = None) -> None:
        """Add a message to conversation history."""
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            topic=topic,
            metadata=metadata or {}
        )
        self.conversation_history.append(message)

        if role == "interviewer":
            self.questions_asked += 1

    def add_evaluation(self, evaluation: ResponseEvaluation) -> None:
        """Add an evaluation to the session."""
        self.evaluations.append(evaluation)

    def get_current_topic(self) -> Optional[Topic]:
        """Get the current topic object."""
        for topic in self.topics:
            if topic.name == self.current_topic:
                return topic
        return None

    def get_average_score(self) -> float:
        """Calculate average score across all evaluations."""
        if not self.evaluations:
            return 0.0
        return sum(e.overall_score for e in self.evaluations) / len(self.evaluations)

    def get_topic_average_score(self, topic_name: str) -> float:
        """Calculate average score for a specific topic."""
        topic_evals = [e for e in self.evaluations if e.topic == topic_name]
        if not topic_evals:
            return 0.0
        return sum(e.overall_score for e in topic_evals) / len(topic_evals)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "candidate_profile": self.candidate_profile.to_dict(),
            "job_requirements": self.job_requirements.to_dict(),
            "topics": [t.to_dict() for t in self.topics],
            "current_topic": self.current_topic,
            "current_topic_index": self.current_topic_index,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "conversation_history": [m.to_dict() for m in self.conversation_history],
            "evaluations": [e.to_dict() for e in self.evaluations],
            "final_report": self.final_report.to_dict() if self.final_report else None,
            "questions_asked": self.questions_asked
        }
