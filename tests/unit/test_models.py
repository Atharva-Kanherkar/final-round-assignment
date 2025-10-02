"""
Comprehensive tests for data models.

Tests model creation, validation, serialization, and methods.
"""
import pytest
from datetime import datetime
from src.models.candidate import CandidateProfile, JobRequirements, Topic
from src.models.session import InterviewSession, Message, SessionStatus
from src.models.evaluation import ResponseEvaluation, TopicSummary, FinalReport


# ============================================================================
# Candidate Profile Tests
# ============================================================================

class TestCandidateProfile:
    """Test CandidateProfile model."""

    def test_create_candidate_profile(self, candidate_profile):
        """Test creating candidate profile."""
        assert candidate_profile.name == "John Doe"
        assert len(candidate_profile.skills) > 0
        assert candidate_profile.experience_years == 5
        assert len(candidate_profile.past_roles) > 0

    def test_candidate_profile_to_dict(self, candidate_profile):
        """Test serialization to dictionary."""
        data = candidate_profile.to_dict()

        assert data["name"] == candidate_profile.name
        assert data["skills"] == candidate_profile.skills
        assert data["experience_years"] == candidate_profile.experience_years
        assert isinstance(data, dict)

    def test_candidate_profile_minimal(self):
        """Test minimal candidate profile."""
        minimal = CandidateProfile(
            name="Jane",
            skills=["Python"],
            experience_years=2,
            education="BS",
            past_roles=[]
        )

        assert minimal.name == "Jane"
        assert len(minimal.skills) == 1


# ============================================================================
# Job Requirements Tests
# ============================================================================

class TestJobRequirements:
    """Test JobRequirements model."""

    def test_create_job_requirements(self, job_requirements):
        """Test creating job requirements."""
        assert job_requirements.title == "Senior Backend Engineer"
        assert job_requirements.company == "TechCo"
        assert len(job_requirements.required_skills) > 0

    def test_job_requirements_to_dict(self, job_requirements):
        """Test serialization to dictionary."""
        data = job_requirements.to_dict()

        assert data["title"] == job_requirements.title
        assert data["company"] == job_requirements.company
        assert isinstance(data["required_skills"], list)

    def test_job_requirements_with_defaults(self):
        """Test job requirements with default values."""
        minimal = JobRequirements(
            title="Engineer",
            company="TestCo",
            required_skills=["Skill1"]
        )

        assert minimal.preferred_skills == []
        assert minimal.responsibilities == []
        assert minimal.experience_required == 0


# ============================================================================
# Topic Tests
# ============================================================================

class TestTopic:
    """Test Topic model."""

    def test_create_topic(self):
        """Test creating topic."""
        topic = Topic(name="Python", priority=5, depth="surface")

        assert topic.name == "Python"
        assert topic.priority == 5
        assert topic.depth == "surface"
        assert topic.questions_asked == 0
        assert topic.covered == False

    def test_topic_to_dict(self):
        """Test topic serialization."""
        topic = Topic(name="AWS", priority=4, depth="deep", questions_asked=3, covered=True)
        data = topic.to_dict()

        assert data["name"] == "AWS"
        assert data["priority"] == 4
        assert data["depth"] == "deep"
        assert data["questions_asked"] == 3
        assert data["covered"] == True


# ============================================================================
# Message Tests
# ============================================================================

class TestMessage:
    """Test Message model."""

    def test_create_message(self):
        """Test creating message."""
        msg = Message(
            role="interviewer",
            content="What is Python?",
            timestamp=datetime.now(),
            topic="Python",
            metadata={"key": "value"}
        )

        assert msg.role == "interviewer"
        assert msg.content == "What is Python?"
        assert msg.topic == "Python"
        assert msg.metadata["key"] == "value"

    def test_message_to_dict(self):
        """Test message serialization."""
        msg = Message(
            role="candidate",
            content="Answer",
            timestamp=datetime.now(),
            topic="Python",
            metadata={}
        )

        data = msg.to_dict()

        assert data["role"] == "candidate"
        assert data["content"] == "Answer"
        assert "timestamp" in data


# ============================================================================
# Interview Session Tests
# ============================================================================

class TestInterviewSession:
    """Test InterviewSession model and methods."""

    def test_create_session(self, interview_session):
        """Test creating interview session."""
        assert interview_session.session_id is not None
        assert interview_session.status == SessionStatus.ACTIVE
        assert len(interview_session.topics) > 0
        assert interview_session.questions_asked == 0

    def test_add_message(self, interview_session):
        """Test adding message to session."""
        initial_count = len(interview_session.conversation_history)

        interview_session.add_message("interviewer", "Question?", "Python")

        assert len(interview_session.conversation_history) == initial_count + 1
        assert interview_session.questions_asked == 1

    def test_add_evaluation(self, interview_session, sample_evaluation):
        """Test adding evaluation to session."""
        initial_count = len(interview_session.evaluations)

        interview_session.add_evaluation(sample_evaluation)

        assert len(interview_session.evaluations) == initial_count + 1

    def test_get_current_topic(self, interview_session):
        """Test getting current topic object."""
        current = interview_session.get_current_topic()

        assert current is not None
        assert current.name == interview_session.current_topic

    def test_get_average_score(self, session_with_evaluations):
        """Test calculating average score."""
        avg = session_with_evaluations.get_average_score()

        assert avg > 0
        assert avg <= 5.0

    def test_get_topic_average_score(self, session_with_evaluations):
        """Test calculating average score for specific topic."""
        avg = session_with_evaluations.get_topic_average_score("Python")

        assert avg > 0
        assert avg <= 5.0

    def test_get_average_score_no_evaluations(self, interview_session):
        """Test average score with no evaluations."""
        avg = interview_session.get_average_score()

        assert avg == 0.0

    def test_session_to_dict(self, interview_session):
        """Test session serialization."""
        data = interview_session.to_dict()

        assert "session_id" in data
        assert "candidate_profile" in data
        assert "job_requirements" in data
        assert "topics" in data
        assert "conversation_history" in data
        assert "evaluations" in data


# ============================================================================
# Evaluation Tests
# ============================================================================

class TestResponseEvaluation:
    """Test ResponseEvaluation model."""

    def test_create_evaluation(self, sample_evaluation):
        """Test creating evaluation."""
        assert sample_evaluation.question is not None
        assert sample_evaluation.overall_score >= 0
        assert sample_evaluation.overall_score <= 5

    def test_evaluation_to_dict(self, sample_evaluation):
        """Test evaluation serialization."""
        data = sample_evaluation.to_dict()

        assert "question" in data
        assert "response" in data
        assert "scores" in data
        assert data["scores"]["overall"] == sample_evaluation.overall_score

    def test_evaluation_score_bounds(self):
        """Test evaluation scores are within bounds."""
        eval = ResponseEvaluation(
            question="Test",
            response="Answer",
            topic="Python",
            timestamp=datetime.now(),
            technical_accuracy=4.0,
            depth=3.5,
            clarity=5.0,
            relevance=4.5,
            overall_score=4.25
        )

        # All scores should be 0-5
        assert 0 <= eval.technical_accuracy <= 5
        assert 0 <= eval.depth <= 5
        assert 0 <= eval.clarity <= 5
        assert 0 <= eval.relevance <= 5
        assert 0 <= eval.overall_score <= 5


# ============================================================================
# Final Report Tests
# ============================================================================

class TestFinalReport:
    """Test FinalReport model."""

    def test_create_final_report(self):
        """Test creating final report."""
        report = FinalReport(
            session_id="test-123",
            candidate_name="John Doe",
            job_title="Engineer",
            interview_date=datetime.now(),
            duration_minutes=25.5,
            total_questions=10,
            topics_covered=["Python", "AWS"],
            overall_score=4.2
        )

        assert report.session_id == "test-123"
        assert report.total_questions == 10
        assert len(report.topics_covered) == 2
        assert report.overall_score == 4.2

    def test_final_report_to_dict(self):
        """Test final report serialization."""
        report = FinalReport(
            session_id="test-123",
            candidate_name="John",
            job_title="Engineer",
            interview_date=datetime.now(),
            duration_minutes=20.0,
            total_questions=8,
            topics_covered=["Python"],
            overall_score=3.5,
            recommendation="Hire"
        )

        data = report.to_dict()

        assert data["session_id"] == "test-123"
        assert data["overall_score"] == 3.5
        assert data["recommendation"] == "Hire"


# ============================================================================
# Model Edge Cases
# ============================================================================

class TestModelEdgeCases:
    """Test edge cases in models."""

    def test_empty_skills_list(self):
        """Test candidate with empty skills."""
        profile = CandidateProfile(
            name="Test",
            skills=[],
            experience_years=0,
            education="None",
            past_roles=[]
        )

        assert len(profile.skills) == 0

    def test_zero_experience(self):
        """Test candidate with zero experience."""
        profile = CandidateProfile(
            name="Graduate",
            skills=["Python"],
            experience_years=0,
            education="BS",
            past_roles=[]
        )

        assert profile.experience_years == 0

    def test_topic_with_zero_questions(self):
        """Test topic with zero questions asked."""
        topic = Topic(name="Test", priority=5)

        assert topic.questions_asked == 0
        assert not topic.covered

    def test_session_with_no_evaluations(self, interview_session):
        """Test session operations with no evaluations."""
        assert len(interview_session.evaluations) == 0
        assert interview_session.get_average_score() == 0.0
        assert interview_session.get_topic_average_score("Python") == 0.0
