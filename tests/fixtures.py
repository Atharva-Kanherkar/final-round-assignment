"""Comprehensive test fixtures and test data."""
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from src.models.candidate import CandidateProfile, JobRequirements, Topic
from src.models.session import InterviewSession, SessionStatus
from src.models.evaluation import ResponseEvaluation


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def valid_resume_text():
    """Valid resume text for testing."""
    return """John Doe
Senior Software Engineer
5 years experience

Skills: Python, JavaScript, React, Node.js, AWS, Docker, Kubernetes, PostgreSQL, MongoDB, Redis, Git, CI/CD, System Design

Experience:
- Tech Corp (2020-2023): Led backend development for microservices architecture serving 1M+ users. Designed and implemented RESTful APIs using Python/Django and Node.js. Migrated monolithic application to containerized microservices using Docker and Kubernetes. Reduced API response time by 40% through optimization and caching strategies with Redis. Mentored 3 junior developers and conducted code reviews.

- StartupXYZ (2018-2020): Full-stack development using React and Node.js. Built user authentication and authorization system with JWT tokens. Implemented real-time features using WebSockets. Integrated third-party payment APIs (Stripe). Contributed to increasing user base from 10K to 100K users.

Education: BS Computer Science, State University (2014-2018)

Projects:
- Developed an open-source task management tool using Python Flask and React
- Built a distributed caching system as part of university research project
- Contributed to several open-source projects on GitHub

Certifications:
- AWS Certified Solutions Architect - Associate
- Certified Kubernetes Administrator (CKA)
"""


@pytest.fixture
def valid_job_description_text():
    """Valid job description text for testing."""
    return """Senior Backend Engineer
Company: TechCo

Requirements:
- 5+ years Python experience
- Strong system design skills
- Experience with distributed systems
- AWS/Cloud experience required
- Experience with microservices architecture
- Proficiency in SQL and NoSQL databases
- Experience with Docker and Kubernetes
- Strong understanding of RESTful API design
- Leadership experience preferred
- Excellent problem-solving and communication skills

Responsibilities:
- Design scalable backend services handling millions of requests
- Lead technical initiatives and architecture decisions
- Mentor junior engineers and conduct code reviews
- Collaborate with frontend team and product managers
- Optimize system performance and reliability
- Implement monitoring and observability solutions
- Participate in on-call rotation
- Drive best practices for testing and deployment

Nice to Have:
- Experience with message queues (RabbitMQ, Kafka)
- Knowledge of GraphQL
- Open-source contributions
- Experience with Infrastructure as Code (Terraform)

About TechCo:
TechCo is a fast-growing technology company building innovative solutions for enterprise customers. We value technical excellence, collaboration, and continuous learning.
"""


@pytest.fixture
def minimal_resume_text():
    """Minimal but valid resume."""
    return """Jane Smith
Software Developer

Skills: Python, Java
Experience: 3 years at ABC Corp
Education: BS Computer Science
"""


@pytest.fixture
def candidate_profile():
    """Sample candidate profile."""
    return CandidateProfile(
        name="John Doe",
        skills=["Python", "JavaScript", "React", "Node.js", "AWS", "Docker", "Kubernetes"],
        experience_years=5,
        education="BS Computer Science, State University",
        past_roles=[
            {"company": "Tech Corp", "role": "Senior Software Engineer", "duration": "2020-2023"},
            {"company": "StartupXYZ", "role": "Full-stack Developer", "duration": "2018-2020"}
        ],
        summary="John Doe - 5 years experience in Python, JavaScript, React",
        raw_resume="[resume text]"
    )


@pytest.fixture
def job_requirements():
    """Sample job requirements."""
    return JobRequirements(
        title="Senior Backend Engineer",
        company="TechCo",
        required_skills=[
            "5+ years Python experience",
            "Strong system design skills",
            "Experience with distributed systems",
            "AWS/Cloud experience",
            "Microservices architecture"
        ],
        preferred_skills=[
            "Message queues (RabbitMQ, Kafka)",
            "GraphQL",
            "Open-source contributions"
        ],
        responsibilities=[
            "Design scalable backend services",
            "Lead technical initiatives",
            "Mentor junior engineers"
        ],
        experience_required=5,
        raw_description="[job description text]"
    )


@pytest.fixture
def sample_topics():
    """Sample interview topics."""
    return [
        Topic(name="Python", priority=5, depth="surface", questions_asked=0, covered=False),
        Topic(name="System Design", priority=5, depth="surface", questions_asked=0, covered=False),
        Topic(name="AWS", priority=4, depth="surface", questions_asked=0, covered=False),
        Topic(name="Docker", priority=4, depth="surface", questions_asked=0, covered=False),
        Topic(name="Microservices", priority=3, depth="surface", questions_asked=0, covered=False)
    ]


@pytest.fixture
def interview_session(candidate_profile, job_requirements, sample_topics):
    """Sample interview session."""
    return InterviewSession(
        session_id="test-session-123",
        candidate_profile=candidate_profile,
        job_requirements=job_requirements,
        topics=sample_topics,
        current_topic="Python",
        current_topic_index=0,
        status=SessionStatus.ACTIVE,
        start_time=datetime.now()
    )


@pytest.fixture
def sample_evaluation():
    """Sample response evaluation."""
    return ResponseEvaluation(
        question="What is Python and why is it popular?",
        response="Python is a high-level programming language...",
        topic="Python",
        timestamp=datetime.now(),
        technical_accuracy=4.0,
        depth=3.5,
        clarity=4.5,
        relevance=4.0,
        overall_score=4.0,
        strengths=["Clear explanation", "Good examples"],
        gaps=["Could mention more use cases"],
        feedback="Good answer with clear examples."
    )


# ============================================================================
# Mock LLM Response Fixtures
# ============================================================================

@pytest.fixture
def mock_llm_question_response():
    """Mock LLM response for question generation."""
    return {
        "question": "Can you explain the difference between Python lists and tuples, and when you would use each?",
        "reasoning": "Tests fundamental Python knowledge and understanding of data structures",
        "expected_elements": [
            "Lists are mutable, tuples are immutable",
            "Performance differences",
            "Use cases for each"
        ]
    }


@pytest.fixture
def mock_llm_evaluation_response():
    """Mock LLM response for evaluation."""
    return {
        "technical_accuracy": 4.0,
        "depth": 3.5,
        "clarity": 4.5,
        "relevance": 4.0,
        "strengths": [
            "Clear explanation of mutability",
            "Good examples provided",
            "Mentioned performance implications"
        ],
        "gaps": [
            "Could have discussed memory usage",
            "Didn't mention named tuples"
        ],
        "feedback": "Strong answer demonstrating good understanding of Python fundamentals. Consider exploring advanced tuple features like named tuples in future discussions."
    }


@pytest.fixture
def mock_llm_topic_transition_response():
    """Mock LLM response for topic transition."""
    return {
        "next_topic": "System Design",
        "depth": "surface",
        "reasoning": "Candidate showed strong Python fundamentals, ready to move to system design"
    }


# ============================================================================
# Mock Objects
# ============================================================================

@pytest.fixture
def mock_llm_client():
    """Mock LLM client with pre-configured responses."""
    mock = Mock()

    # Default successful responses
    mock.generate_text = AsyncMock(return_value="Sample text response")
    mock.generate_structured = AsyncMock(return_value={
        "question": "Sample question?",
        "reasoning": "Sample reasoning",
        "expected_elements": ["Element 1", "Element 2"]
    })

    return mock


@pytest.fixture
def mock_logger():
    """Mock logger."""
    logger = Mock()
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    return logger


@pytest.fixture
def mock_config():
    """Mock configuration."""
    return {
        "min_questions_per_topic": 2,
        "max_questions_per_topic": 4,
        "total_topics_target": 5,
        "timeout_seconds": 30,
        "max_retries": 3
    }


# ============================================================================
# Edge Case Data
# ============================================================================

@pytest.fixture
def malicious_resume_xss():
    """Resume with XSS attempt."""
    return "<script>alert('xss')</script>" + ("John Doe\nSoftware Engineer\n" * 10)


@pytest.fixture
def malicious_resume_path_traversal():
    """Resume with path traversal attempt."""
    return "../../etc/passwd\n" + ("John Doe\nSoftware Engineer\n" * 10)


@pytest.fixture
def binary_resume():
    """Binary data disguised as resume."""
    return "\x00\x01\x02\x03\x04" * 200


@pytest.fixture
def empty_resume():
    """Empty resume."""
    return ""


@pytest.fixture
def whitespace_resume():
    """Whitespace-only resume."""
    return "   \n\n\t\t  \n  "


@pytest.fixture
def oversized_resume():
    """Resume exceeding size limit."""
    return "A" * 600000  # 600KB


@pytest.fixture
def resume_with_no_skills():
    """Resume with no detectable skills."""
    return """John Doe
Person

I worked at places doing things.
I have education.
I like computers.
""" * 3


# ============================================================================
# API Error Scenarios
# ============================================================================

@pytest.fixture
def mock_rate_limit_error():
    """Mock rate limit error."""
    from openai import RateLimitError
    return RateLimitError("Rate limit exceeded", response=Mock(status_code=429), body=None)


@pytest.fixture
def mock_timeout_error():
    """Mock timeout error."""
    from openai import APITimeoutError
    return APITimeoutError(request=Mock())


@pytest.fixture
def mock_api_error():
    """Mock general API error."""
    from openai import APIError
    return APIError("Internal server error", request=Mock(), body=None)


@pytest.fixture
def mock_invalid_json_response():
    """Mock response with invalid JSON."""
    return "This is not JSON at all, just plain text"


@pytest.fixture
def mock_empty_response():
    """Mock empty response."""
    return ""


# ============================================================================
# Complex Scenarios
# ============================================================================

@pytest.fixture
def multi_turn_conversation(interview_session):
    """Session with multiple conversation turns."""
    from src.models.session import Message

    # Add some conversation history
    interview_session.add_message(
        "interviewer",
        "What is Python?",
        "Python",
        {"expected_elements": ["Language features", "Use cases"]}
    )
    interview_session.add_message(
        "candidate",
        "Python is a high-level programming language...",
        "Python"
    )
    interview_session.add_message(
        "interviewer",
        "How do you handle concurrency in Python?",
        "Python",
        {"expected_elements": ["Threading", "Async/await", "GIL"]}
    )
    interview_session.add_message(
        "candidate",
        "Python has several approaches to concurrency...",
        "Python"
    )

    return interview_session


@pytest.fixture
def session_with_evaluations(interview_session, sample_evaluation):
    """Session with multiple evaluations."""
    # Add multiple evaluations
    for i in range(5):
        eval_copy = ResponseEvaluation(
            question=f"Question {i+1}",
            response=f"Response {i+1}",
            topic="Python",
            timestamp=datetime.now(),
            technical_accuracy=4.0 - (i * 0.2),
            depth=3.5,
            clarity=4.0,
            relevance=4.0,
            overall_score=3.8 - (i * 0.1),
            strengths=["Good understanding"],
            gaps=["Could be more detailed"],
            feedback="Solid answer"
        )
        interview_session.add_evaluation(eval_copy)

    return interview_session


# ============================================================================
# Performance Testing Data
# ============================================================================

@pytest.fixture
def large_conversation_history():
    """Large conversation history for performance testing."""
    from src.models.session import Message

    messages = []
    for i in range(100):
        messages.append(Message(
            role="interviewer" if i % 2 == 0 else "candidate",
            content=f"Message content {i}" * 50,  # Make it reasonably large
            timestamp=datetime.now(),
            topic="Python",
            metadata={}
        ))
    return messages


@pytest.fixture
def stress_test_config():
    """Configuration for stress testing."""
    return {
        "concurrent_sessions": 10,
        "questions_per_session": 20,
        "response_size": 5000,  # characters
        "timeout": 60
    }
