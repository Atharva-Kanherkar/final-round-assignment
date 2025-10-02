"""
Comprehensive unit tests for all agents.

Tests each agent in isolation with mocked dependencies.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.agents.interviewer import InterviewerAgent
from src.agents.evaluator import EvaluatorAgent
from src.agents.topic_manager import TopicManagerAgent
from src.agents.orchestrator import OrchestratorAgent
from src.models.candidate import Topic
from src.models.session import SessionStatus
from src.utils.exceptions import AgentExecutionError, AgentValidationError


# ============================================================================
# Interviewer Agent Tests
# ============================================================================

class TestInterviewerAgent:
    """Test InterviewerAgent functionality."""

    @pytest.mark.asyncio
    async def test_successful_question_generation(self, mock_llm_client, mock_logger, candidate_profile, job_requirements, mock_llm_question_response):
        """Test successful question generation."""
        # Setup
        mock_llm_client.generate_structured = AsyncMock(return_value=mock_llm_question_response)
        agent = InterviewerAgent(mock_llm_client, mock_logger)

        context = {
            "candidate_profile": candidate_profile,
            "job_requirements": job_requirements,
            "current_topic": "Python",
            "topic_depth": "surface",
            "conversation_history": [],
            "last_evaluation": None
        }

        # Execute
        result = await agent.execute(context)

        # Assert
        assert "question" in result
        assert "reasoning" in result
        assert "expected_elements" in result
        assert len(result["question"]) > 0
        assert isinstance(result["expected_elements"], list)
        mock_llm_client.generate_structured.assert_called_once()

    @pytest.mark.asyncio
    async def test_question_generation_with_conversation_history(self, mock_llm_client, mock_logger, multi_turn_conversation):
        """Test question generation considers previous conversation."""
        # Setup
        mock_llm_client.generate_structured = AsyncMock(return_value={
            "question": "Follow-up question based on previous answers",
            "reasoning": "Building on previous discussion",
            "expected_elements": ["Advanced concept"]
        })
        agent = InterviewerAgent(mock_llm_client, mock_logger)

        context = {
            "candidate_profile": multi_turn_conversation.candidate_profile,
            "job_requirements": multi_turn_conversation.job_requirements,
            "current_topic": "Python",
            "topic_depth": "deep",
            "conversation_history": multi_turn_conversation.conversation_history,
            "last_evaluation": None
        }

        # Execute
        result = await agent.execute(context)

        # Assert
        assert result["question"] is not None
        # Verify the prompt included conversation context
        call_args = mock_llm_client.generate_structured.call_args
        prompt = call_args[1]["prompt"]
        assert "Recent Conversation" in prompt or "previous" in prompt.lower()

    @pytest.mark.asyncio
    async def test_question_generation_depth_variation(self, mock_llm_client, mock_logger, candidate_profile, job_requirements):
        """Test questions vary by depth (surface vs deep)."""
        agent = InterviewerAgent(mock_llm_client, mock_logger)

        # Test surface depth
        mock_llm_client.generate_structured = AsyncMock(return_value={
            "question": "What is Python?",
            "reasoning": "Basic knowledge check",
            "expected_elements": ["Programming language", "Features"]
        })

        context_surface = {
            "candidate_profile": candidate_profile,
            "job_requirements": job_requirements,
            "current_topic": "Python",
            "topic_depth": "surface",
            "conversation_history": [],
            "last_evaluation": None
        }

        result_surface = await agent.execute(context_surface)

        # Test deep depth
        mock_llm_client.generate_structured = AsyncMock(return_value={
            "question": "Explain Python's GIL and its implications for multi-threading",
            "reasoning": "Deep technical knowledge",
            "expected_elements": ["GIL explanation", "Threading limitations", "Workarounds"]
        })

        context_deep = {
            **context_surface,
            "topic_depth": "deep"
        }

        result_deep = await agent.execute(context_deep)

        # Assert both succeeded
        assert result_surface["question"] is not None
        assert result_deep["question"] is not None

    @pytest.mark.asyncio
    async def test_question_generation_api_failure_fallback(self, mock_llm_client, mock_logger, candidate_profile, job_requirements):
        """Test fallback question when LLM fails."""
        # Setup - make LLM fail
        mock_llm_client.generate_structured = AsyncMock(side_effect=Exception("API Error"))
        agent = InterviewerAgent(mock_llm_client, mock_logger)

        context = {
            "candidate_profile": candidate_profile,
            "job_requirements": job_requirements,
            "current_topic": "Python",
            "topic_depth": "surface",
            "conversation_history": [],
            "last_evaluation": None
        }

        # Execute
        result = await agent.execute(context)

        # Assert - should return fallback question
        assert "question" in result
        assert "Python" in result["question"]
        assert "fallback" in result["reasoning"].lower() or "error" in result["reasoning"].lower()

    @pytest.mark.asyncio
    async def test_question_considers_last_evaluation(self, mock_llm_client, mock_logger, candidate_profile, job_requirements, sample_evaluation):
        """Test question generation adjusts based on last evaluation."""
        mock_llm_client.generate_structured = AsyncMock(return_value={
            "question": "Adjusted question based on performance",
            "reasoning": "Following up on previous answer",
            "expected_elements": ["Element"]
        })
        agent = InterviewerAgent(mock_llm_client, mock_logger)

        context = {
            "candidate_profile": candidate_profile,
            "job_requirements": job_requirements,
            "current_topic": "Python",
            "topic_depth": "surface",
            "conversation_history": [],
            "last_evaluation": sample_evaluation
        }

        # Execute
        result = await agent.execute(context)

        # Assert
        assert result is not None
        # Verify evaluation context was included in prompt
        call_args = mock_llm_client.generate_structured.call_args
        prompt = call_args[1]["prompt"]
        assert "Score" in prompt or "evaluation" in prompt.lower()


# ============================================================================
# Evaluator Agent Tests
# ============================================================================

class TestEvaluatorAgent:
    """Test EvaluatorAgent functionality."""

    @pytest.mark.asyncio
    async def test_successful_evaluation(self, mock_llm_client, mock_logger, mock_llm_evaluation_response, candidate_profile):
        """Test successful response evaluation."""
        # Setup
        mock_llm_client.generate_structured = AsyncMock(return_value=mock_llm_evaluation_response)
        agent = EvaluatorAgent(mock_llm_client, mock_logger)

        context = {
            "question": "What is Python?",
            "response": "Python is a high-level programming language known for its simplicity...",
            "topic": "Python",
            "expected_elements": ["High-level language", "Simplicity", "Use cases"],
            "candidate_profile": candidate_profile
        }

        # Execute
        result = await agent.execute(context)

        # Assert
        assert "evaluation" in result
        eval_obj = result["evaluation"]
        assert eval_obj.overall_score >= 0 and eval_obj.overall_score <= 5
        assert eval_obj.technical_accuracy >= 0 and eval_obj.technical_accuracy <= 5
        assert eval_obj.depth >= 0 and eval_obj.depth <= 5
        assert eval_obj.clarity >= 0 and eval_obj.clarity <= 5
        assert eval_obj.relevance >= 0 and eval_obj.relevance <= 5
        assert isinstance(eval_obj.strengths, list)
        assert isinstance(eval_obj.gaps, list)
        assert len(eval_obj.feedback) > 0

    @pytest.mark.asyncio
    async def test_evaluation_score_calculation(self, mock_llm_client, mock_logger, candidate_profile):
        """Test overall score is calculated correctly."""
        # Setup - return specific scores
        mock_llm_client.generate_structured = AsyncMock(return_value={
            "technical_accuracy": 4.0,
            "depth": 3.0,
            "clarity": 5.0,
            "relevance": 4.0,
            "strengths": ["Good"],
            "gaps": ["Could improve"],
            "feedback": "Nice work"
        })
        agent = EvaluatorAgent(mock_llm_client, mock_logger)

        context = {
            "question": "Test question",
            "response": "Test response",
            "topic": "Python",
            "expected_elements": [],
            "candidate_profile": candidate_profile
        }

        # Execute
        result = await agent.execute(context)

        # Assert - overall should be average of 4 dimensions
        expected_overall = (4.0 + 3.0 + 5.0 + 4.0) / 4.0
        assert result["evaluation"].overall_score == expected_overall

    @pytest.mark.asyncio
    async def test_evaluation_empty_response(self, mock_llm_client, mock_logger, candidate_profile):
        """Test evaluation of empty/minimal response."""
        mock_llm_client.generate_structured = AsyncMock(return_value={
            "technical_accuracy": 1.0,
            "depth": 0.5,
            "clarity": 2.0,
            "relevance": 1.0,
            "strengths": [],
            "gaps": ["No substantial content", "Too brief"],
            "feedback": "Response lacks depth and detail. Please provide more comprehensive answers."
        })
        agent = EvaluatorAgent(mock_llm_client, mock_logger)

        context = {
            "question": "Explain Python's memory management",
            "response": "I don't know",
            "topic": "Python",
            "expected_elements": ["Garbage collection", "Reference counting"],
            "candidate_profile": candidate_profile
        }

        # Execute
        result = await agent.execute(context)

        # Assert - should have low scores
        assert result["evaluation"].overall_score < 2.0
        assert len(result["evaluation"].gaps) > 0

    @pytest.mark.asyncio
    async def test_evaluation_api_failure_fallback(self, mock_llm_client, mock_logger, candidate_profile):
        """Test fallback evaluation when LLM fails."""
        # Setup - make LLM fail
        mock_llm_client.generate_structured = AsyncMock(side_effect=Exception("API Error"))
        agent = EvaluatorAgent(mock_llm_client, mock_logger)

        context = {
            "question": "Test question",
            "response": "Test response",
            "topic": "Python",
            "expected_elements": [],
            "candidate_profile": candidate_profile
        }

        # Execute
        result = await agent.execute(context)

        # Assert - should return fallback evaluation
        assert "evaluation" in result
        assert result["evaluation"].overall_score == 3.0  # Default fallback score
        assert "technical error" in result["evaluation"].feedback.lower() or "unable" in result["evaluation"].feedback.lower()


# ============================================================================
# Topic Manager Agent Tests
# ============================================================================

class TestTopicManagerAgent:
    """Test TopicManagerAgent functionality."""

    @pytest.mark.asyncio
    async def test_no_transition_min_questions_not_met(self, mock_llm_client, mock_logger, sample_topics):
        """Test no transition when minimum questions not met."""
        agent = TopicManagerAgent(mock_llm_client, mock_logger)

        context = {
            "current_topic": sample_topics[0],
            "all_topics": sample_topics,
            "recent_scores": [4.0],
            "questions_in_topic": 1,  # Less than min (2)
            "total_questions": 1,
            "min_questions_per_topic": 2,
            "max_questions_per_topic": 4,
            "candidate_profile": Mock(),
            "job_requirements": Mock()
        }

        # Execute
        result = await agent.execute(context)

        # Assert
        assert result["should_transition"] == False
        assert "minimum" in result["reasoning"].lower()

    @pytest.mark.asyncio
    async def test_force_transition_max_questions_reached(self, mock_llm_client, mock_logger, sample_topics):
        """Test forced transition when max questions reached."""
        mock_llm_client.generate_structured = AsyncMock(return_value={
            "next_topic": "System Design",
            "depth": "surface",
            "reasoning": "Moving to next topic"
        })
        agent = TopicManagerAgent(mock_llm_client, mock_logger)

        context = {
            "current_topic": sample_topics[0],
            "all_topics": sample_topics,
            "recent_scores": [3.5, 3.8, 4.0, 3.9],
            "questions_in_topic": 4,  # At max
            "total_questions": 4,
            "min_questions_per_topic": 2,
            "max_questions_per_topic": 4,
            "candidate_profile": Mock(),
            "job_requirements": Mock()
        }

        # Execute
        result = await agent.execute(context)

        # Assert
        assert result["should_transition"] == True
        assert "maximum" in result["reasoning"].lower() or "max" in result["reasoning"].lower()

    @pytest.mark.asyncio
    async def test_transition_high_performance(self, mock_llm_client, mock_logger, sample_topics):
        """Test transition when performance is high."""
        mock_llm_client.generate_structured = AsyncMock(return_value={
            "next_topic": "System Design",
            "depth": "surface",
            "reasoning": "Strong performance, moving forward"
        })
        agent = TopicManagerAgent(mock_llm_client, mock_logger)

        context = {
            "current_topic": sample_topics[0],
            "all_topics": sample_topics,
            "recent_scores": [4.5, 4.3],  # High scores
            "questions_in_topic": 2,  # Min questions met
            "total_questions": 2,
            "min_questions_per_topic": 2,
            "max_questions_per_topic": 4,
            "candidate_profile": Mock(),
            "job_requirements": Mock()
        }

        # Execute
        result = await agent.execute(context)

        # Assert
        assert result["should_transition"] == True
        assert result["next_topic"] == "System Design"

    @pytest.mark.asyncio
    async def test_no_transition_low_performance(self, mock_llm_client, mock_logger, sample_topics):
        """Test no transition when performance is low."""
        agent = TopicManagerAgent(mock_llm_client, mock_logger)

        context = {
            "current_topic": sample_topics[0],
            "all_topics": sample_topics,
            "recent_scores": [2.5, 2.8],  # Low scores
            "questions_in_topic": 2,  # Min questions met
            "total_questions": 2,
            "min_questions_per_topic": 2,
            "max_questions_per_topic": 4,
            "candidate_profile": Mock(),
            "job_requirements": Mock()
        }

        # Execute
        result = await agent.execute(context)

        # Assert
        assert result["should_transition"] == False

    @pytest.mark.asyncio
    async def test_depth_increase_good_performance(self, mock_llm_client, mock_logger, sample_topics):
        """Test depth increases when performance is good."""
        agent = TopicManagerAgent(mock_llm_client, mock_logger)

        current_topic = sample_topics[0]
        current_topic.depth = "surface"

        context = {
            "current_topic": current_topic,
            "all_topics": sample_topics,
            "recent_scores": [4.0, 4.2],  # Good scores
            "questions_in_topic": 2,
            "total_questions": 2,
            "min_questions_per_topic": 2,
            "max_questions_per_topic": 4,
            "candidate_profile": Mock(),
            "job_requirements": Mock()
        }

        # Execute
        result = await agent.execute(context)

        # Assert - if not transitioning, depth should increase
        if not result["should_transition"]:
            assert result["next_depth"] == "deep"

    @pytest.mark.asyncio
    async def test_single_topic_remaining(self, mock_llm_client, mock_logger, sample_topics):
        """Test behavior when only one topic remains."""
        # Mark all but one as covered
        for topic in sample_topics[:-1]:
            topic.covered = True

        agent = TopicManagerAgent(mock_llm_client, mock_logger)

        context = {
            "current_topic": sample_topics[-2],
            "all_topics": sample_topics,
            "recent_scores": [4.0, 4.0],
            "questions_in_topic": 2,
            "total_questions": 8,
            "min_questions_per_topic": 2,
            "max_questions_per_topic": 4,
            "candidate_profile": Mock(),
            "job_requirements": Mock()
        }

        # Execute
        result = await agent.execute(context)

        # Assert
        if result["should_transition"]:
            assert result["next_topic"] == sample_topics[-1].name


# ============================================================================
# Orchestrator Agent Tests
# ============================================================================

class TestOrchestratorAgent:
    """Test OrchestratorAgent functionality."""

    def test_create_session(self, mock_llm_client, mock_logger, candidate_profile, job_requirements, sample_topics):
        """Test session creation."""
        orchestrator = OrchestratorAgent(mock_llm_client, mock_logger)

        session = orchestrator.create_session(candidate_profile, job_requirements, sample_topics)

        assert session is not None
        assert session.session_id is not None
        assert session.candidate_profile == candidate_profile
        assert session.job_requirements == job_requirements
        assert len(session.topics) == len(sample_topics)
        assert session.current_topic == sample_topics[0].name
        assert session.status == SessionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_generate_first_question(self, mock_llm_client, mock_logger, interview_session, mock_llm_question_response):
        """Test first question generation."""
        mock_llm_client.generate_structured = AsyncMock(return_value=mock_llm_question_response)
        orchestrator = OrchestratorAgent(mock_llm_client, mock_logger)

        result = await orchestrator.generate_first_question(interview_session)

        assert "question" in result
        assert len(interview_session.conversation_history) == 1
        assert interview_session.conversation_history[0].role == "interviewer"

    @pytest.mark.asyncio
    async def test_process_response_evaluates_and_generates_next(self, mock_llm_client, mock_logger, interview_session, mock_config):
        """Test processing response evaluates and generates next question."""
        # Setup mocks
        mock_llm_client.generate_structured = AsyncMock(side_effect=[
            # First call: evaluation
            {
                "technical_accuracy": 4.0,
                "depth": 3.5,
                "clarity": 4.5,
                "relevance": 4.0,
                "strengths": ["Clear"],
                "gaps": [],
                "feedback": "Good"
            },
            # Second call: next question
            {
                "question": "Next question?",
                "reasoning": "Following up",
                "expected_elements": ["Element"]
            }
        ])

        orchestrator = OrchestratorAgent(mock_llm_client, mock_logger)

        # Add initial question to history
        interview_session.add_message("interviewer", "What is Python?", "Python", {"expected_elements": []})

        # Execute
        result = await orchestrator.process_response(
            interview_session,
            "Python is a programming language...",
            mock_config
        )

        # Assert
        assert "evaluation" in result
        assert "next_question" in result
        assert result["evaluation"] is not None
        assert len(interview_session.evaluations) == 1

    @pytest.mark.asyncio
    async def test_process_response_handles_topic_transition(self, mock_llm_client, mock_logger, interview_session, mock_config):
        """Test topic transition during response processing."""
        # Setup - make it transition after 2 questions
        interview_session.topics[0].questions_asked = 1  # Will be 2 after this response

        mock_llm_client.generate_structured = AsyncMock(side_effect=[
            # Evaluation
            {
                "technical_accuracy": 4.5,
                "depth": 4.0,
                "clarity": 4.5,
                "relevance": 4.5,
                "strengths": ["Excellent"],
                "gaps": [],
                "feedback": "Perfect"
            },
            # Topic transition decision would happen here (done by TopicManager)
            # Next question
            {
                "question": "System design question?",
                "reasoning": "New topic",
                "expected_elements": ["Architecture"]
            }
        ])

        orchestrator = OrchestratorAgent(mock_llm_client, mock_logger)

        # Add initial question
        interview_session.add_message("interviewer", "Previous question?", "Python", {"expected_elements": []})

        # Execute
        result = await orchestrator.process_response(
            interview_session,
            "Excellent detailed response...",
            mock_config
        )

        # Assert
        assert "transitioned" in result
        assert "evaluation" in result


@pytest.mark.asyncio
async def test_all_agents_initialized():
    """Test all agents can be initialized."""
    from src.agents.base import BaseAgent
    from src.agents.interviewer import InterviewerAgent
    from src.agents.evaluator import EvaluatorAgent
    from src.agents.topic_manager import TopicManagerAgent
    from src.agents.orchestrator import OrchestratorAgent

    mock_llm = Mock()
    mock_logger = Mock()

    # All should initialize without error
    interviewer = InterviewerAgent(mock_llm, mock_logger)
    evaluator = EvaluatorAgent(mock_llm, mock_logger)
    topic_manager = TopicManagerAgent(mock_llm, mock_logger)
    orchestrator = OrchestratorAgent(mock_llm, mock_logger)

    assert interviewer is not None
    assert evaluator is not None
    assert topic_manager is not None
    assert orchestrator is not None
