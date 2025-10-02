"""Data models for evaluation and feedback."""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime


@dataclass
class ResponseEvaluation:
    """Evaluation of a single candidate response."""
    question: str
    response: str
    topic: str
    timestamp: datetime

    # Scores (0-5)
    technical_accuracy: float
    depth: float
    clarity: float
    relevance: float
    overall_score: float

    # Feedback
    strengths: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    feedback: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "question": self.question,
            "response": self.response,
            "topic": self.topic,
            "timestamp": self.timestamp.isoformat(),
            "scores": {
                "technical_accuracy": self.technical_accuracy,
                "depth": self.depth,
                "clarity": self.clarity,
                "relevance": self.relevance,
                "overall": self.overall_score
            },
            "strengths": self.strengths,
            "gaps": self.gaps,
            "feedback": self.feedback
        }


@dataclass
class TopicSummary:
    """Summary of performance in a topic."""
    topic: str
    questions_count: int
    average_score: float
    strengths: List[str]
    areas_for_improvement: List[str]


@dataclass
class FinalReport:
    """Final interview evaluation report."""
    session_id: str
    candidate_name: str
    job_title: str
    interview_date: datetime
    duration_minutes: float

    # Overall metrics
    total_questions: int
    topics_covered: List[str]
    overall_score: float  # 0-5

    # Performance breakdown
    topic_summaries: List[TopicSummary] = field(default_factory=list)

    # Narrative feedback
    overall_strengths: List[str] = field(default_factory=list)
    areas_for_improvement: List[str] = field(default_factory=list)
    recommendation: str = ""  # "Strong hire" | "Hire" | "Maybe" | "No hire"
    additional_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "candidate_name": self.candidate_name,
            "job_title": self.job_title,
            "interview_date": self.interview_date.isoformat(),
            "duration_minutes": self.duration_minutes,
            "total_questions": self.total_questions,
            "topics_covered": self.topics_covered,
            "overall_score": self.overall_score,
            "topic_summaries": [
                {
                    "topic": ts.topic,
                    "questions_count": ts.questions_count,
                    "average_score": ts.average_score,
                    "strengths": ts.strengths,
                    "areas_for_improvement": ts.areas_for_improvement
                }
                for ts in self.topic_summaries
            ],
            "overall_strengths": self.overall_strengths,
            "areas_for_improvement": self.areas_for_improvement,
            "recommendation": self.recommendation,
            "additional_notes": self.additional_notes
        }
