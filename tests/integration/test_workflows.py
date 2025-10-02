"""
Integration tests for multi-agent workflows.

Tests agent interactions, data flow, and end-to-end scenarios.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.agents.orchestrator import OrchestratorAgent
from src.models.session import SessionStatus


# ============================================================================
# Multi-Agent Workflow Tests
# ============================================================================

class TestMultiAgentWorkflows:
    """Test interactions between multiple agents."""

    @pytest.mark.asyncio
    async def test_complete_interview_flow(self, mock_llm_client, mock_logger, candidate_profile, job_requirements, sample_topics, mock_config):
        """Test complete interview workflow from start to finish."""
        # Setup mock responses for entire flow
        mock_llm_client.generate_structured = AsyncMock(side_effect=[
            # First question
            {
                "question": "What is Python?",
                "reasoning": "Basic check",
                "expected_elements": ["Language", "Features"]
            },
            # First evaluation
            {
                "technical_accuracy": 4.0,
                "depth": 3.5,
                "clarity": 4.5,
                "relevance": 4.0,
                "strengths": ["Clear"],
                "gaps": [],
                "feedback": "Good"
            },
            # Second question
            {
                "question": "Explain Python GIL",
                "reasoning": "Deep knowledge",
                "expected_elements": ["GIL", "Threading"]
            },
            # Second evaluation
            {
                "technical_accuracy": 4.5,
                "depth": 4.0,
                "clarity": 4.0,
                "relevance": 4.5,
                "strengths": ["Excellent"],
                "gaps": [],
                "feedback": "Perfect"
            },
            # Third question (new topic)
            {
                "question": "Design a distributed cache",
                "reasoning": "System design",
                "expected_elements": ["Architecture", "Scaling"]
            }
        ])

        orchestrator = OrchestratorAgent(mock_llm_client, mock_logger)

        # Create session
        session = orchestrator.create_session(candidate_profile, job_requirements, sample_topics)

        # Generate first question
        first_q = await orchestrator.generate_first_question(session)
        assert first_q["question"] == "What is Python?"

        # Process first response
        result1 = await orchestrator.process_response(
            session,
            "Python is a high-level programming language...",
            mock_config
        )

        assert result1["evaluation"] is not None
        assert result1["next_question"] is not None
        assert session.questions_asked == 1
        assert len(session.evaluations) == 1

        # Process second response
        result2 = await orchestrator.process_response(
            session,
            "The GIL is the Global Interpreter Lock...",
            mock_config
        )

        assert result2["evaluation"] is not None
        assert session.questions_asked == 2
        assert len(session.evaluations) == 2

    @pytest.mark.asyncio
    async def test_topic_transition_workflow(self, mock_llm_client, mock_logger, interview_session, mock_config):
        """Test topic transition between agents."""
        # Setup to trigger transition
        interview_session.topics[0].questions_asked = 1

        mock_llm_client.generate_structured = AsyncMock(side_effect=[
            # Evaluation (high score to trigger transition)
            {
                "technical_accuracy": 4.5,
                "depth": 4.5,
                "clarity": 4.5,
                "relevance": 4.5,
                "strengths": ["Excellent"],
                "gaps": [],
                "feedback": "Perfect"
            },
            # Next topic selection
            {
                "next_topic": "System Design",
                "depth": "surface",
                "reasoning": "Strong performance"
            },
            # New question for new topic
            {
                "question": "How would you design a URL shortener?",
                "reasoning": "System design basics",
                "expected_elements": ["Database", "API", "Scaling"]
            }
        ])

        orchestrator = OrchestratorAgent(mock_llm_client, mock_logger)

        # Add initial question to history
        interview_session.add_message("interviewer", "Previous question?", "Python", {"expected_elements": []})

        # Process response that should trigger transition
        result = await orchestrator.process_response(
            interview_session,
            "Excellent detailed answer about Python...",
            mock_config
        )

        # Verify transition occurred
        assert "transitioned" in result
        if result["transitioned"]:
            assert interview_session.current_topic != "Python"
            assert result["next_question"] is not None

    @pytest.mark.asyncio
    async def test_agent_communication_flow(self, mock_llm_client, mock_logger, candidate_profile, job_requirements, sample_topics):
        """Test data flow between agents."""
        orchestrator = OrchestratorAgent(mock_llm_client, mock_logger)

        # Mock responses
        mock_llm_client.generate_structured = AsyncMock(side_effect=[
            # Interviewer generates question
            {
                "question": "Test question",
                "reasoning": "Test",
                "expected_elements": ["Element"]
            },
            # Evaluator evaluates response
            {
                "technical_accuracy": 4.0,
                "depth": 4.0,
                "clarity": 4.0,
                "relevance": 4.0,
                "strengths": ["Good"],
                "gaps": [],
                "feedback": "Nice"
            },
            # Topic manager decides
            # Interviewer generates next question
            {
                "question": "Next question",
                "reasoning": "Follow-up",
                "expected_elements": ["Element"]
            }
        ])

        # Create session and generate question
        session = orchestrator.create_session(candidate_profile, job_requirements, sample_topics)
        first_q = await orchestrator.generate_first_question(session)

        # Process response - this involves multiple agents
        result = await orchestrator.process_response(
            session,
            "Test response",
            {"min_questions_per_topic": 2, "max_questions_per_topic": 4}
        )

        # Verify data flowed through all agents
        assert len(session.conversation_history) > 0
        assert len(session.evaluations) > 0
        assert result["evaluation"] is not None


# ============================================================================
# Error Propagation Tests
# ============================================================================

class TestErrorPropagation:
    """Test error handling across multiple agents."""

    @pytest.mark.asyncio
    async def test_interviewer_failure_propagates(self, mock_llm_client, mock_logger, interview_session, mock_config):
        """Test interviewer failure is handled gracefully."""
        # Make interviewer fail
        mock_llm_client.generate_structured = AsyncMock(side_effect=Exception("LLM Error"))

        orchestrator = OrchestratorAgent(mock_llm_client, mock_logger)

        # Should return fallback question
        result = await orchestrator.generate_first_question(interview_session)

        # Fallback question should be provided
        assert "question" in result
        assert len(result["question"]) > 0

    @pytest.mark.asyncio
    async def test_evaluator_failure_fallback(self, mock_llm_client, mock_logger, interview_session, mock_config):
        """Test evaluator failure uses fallback."""
        mock_llm_client.generate_structured = AsyncMock(side_effect=[
            # Evaluator fails
            Exception("Evaluation error"),
            # Next question still generated
            {
                "question": "Next question",
                "reasoning": "Continue",
                "expected_elements": ["Element"]
            }
        ])

        orchestrator = OrchestratorAgent(mock_llm_client, mock_logger)

        # Add question to history
        interview_session.add_message("interviewer", "Test?", "Python", {"expected_elements": []})

        # Process should handle evaluator failure
        result = await orchestrator.process_response(
            interview_session,
            "Test response",
            mock_config
        )

        # Should have fallback evaluation
        assert result["evaluation"] is not None
        assert result["evaluation"].overall_score == 3.0  # Fallback score


# ============================================================================
# Session State Management Tests
# ============================================================================

class TestSessionStateManagement:
    """Test session state across multi-agent operations."""

    @pytest.mark.asyncio
    async def test_session_state_consistency(self, mock_llm_client, mock_logger, interview_session, mock_config):
        """Test session state remains consistent across operations."""
        mock_llm_client.generate_structured = AsyncMock(side_effect=[
            # Question
            {"question": "Q1", "reasoning": "R1", "expected_elements": ["E1"]},
            # Evaluation
            {"technical_accuracy": 4.0, "depth": 4.0, "clarity": 4.0, "relevance": 4.0,
             "strengths": [], "gaps": [], "feedback": "Good"},
            # Next question
            {"question": "Q2", "reasoning": "R2", "expected_elements": ["E2"]},
        ])

        orchestrator = OrchestratorAgent(mock_llm_client, mock_logger)

        initial_status = interview_session.status
        initial_topic = interview_session.current_topic

        # Generate question
        await orchestrator.generate_first_question(interview_session)

        # Process response
        interview_session.add_message("interviewer", "Test?", "Python", {"expected_elements": []})
        await orchestrator.process_response(interview_session, "Response", mock_config)

        # Verify state consistency
        assert interview_session.status == SessionStatus.ACTIVE
        assert interview_session.session_id is not None
        assert len(interview_session.conversation_history) > 0
        assert interview_session.questions_asked > 0

    @pytest.mark.asyncio
    async def test_conversation_history_maintained(self, mock_llm_client, mock_logger, interview_session, mock_config):
        """Test conversation history is maintained correctly."""
        mock_llm_client.generate_structured = AsyncMock(side_effect=[
            {"question": "Q1", "reasoning": "R1", "expected_elements": []},
            {"technical_accuracy": 4.0, "depth": 4.0, "clarity": 4.0, "relevance": 4.0,
             "strengths": [], "gaps": [], "feedback": "Good"},
            {"question": "Q2", "reasoning": "R2", "expected_elements": []},
        ])

        orchestrator = OrchestratorAgent(mock_llm_client, mock_logger)

        # Generate and respond to multiple questions
        await orchestrator.generate_first_question(interview_session)
        history_after_q1 = len(interview_session.conversation_history)

        interview_session.add_message("candidate", "Answer 1", "Python")
        await orchestrator.process_response(interview_session, "Answer 1", mock_config)

        # History should have grown
        assert len(interview_session.conversation_history) > history_after_q1

        # History should alternate between interviewer and candidate
        roles = [msg.role for msg in interview_session.conversation_history]
        assert "interviewer" in roles
        assert "candidate" in roles


# ============================================================================
# Performance Under Load Tests
# ============================================================================

class TestPerformanceUnderLoad:
    """Test system performance under various loads."""

    @pytest.mark.asyncio
    async def test_multiple_evaluations(self, mock_llm_client, mock_logger, interview_session, mock_config):
        """Test handling multiple evaluations in succession."""
        # Setup repeated mock responses
        eval_response = {
            "technical_accuracy": 4.0,
            "depth": 3.5,
            "clarity": 4.0,
            "relevance": 4.0,
            "strengths": ["Good"],
            "gaps": [],
            "feedback": "Nice"
        }

        question_response = {
            "question": "Next question?",
            "reasoning": "Following up",
            "expected_elements": ["Element"]
        }

        responses = []
        for i in range(10):
            responses.append(eval_response)
            responses.append(question_response)

        mock_llm_client.generate_structured = AsyncMock(side_effect=responses)

        orchestrator = OrchestratorAgent(mock_llm_client, mock_logger)

        # Process multiple responses
        for i in range(5):
            interview_session.add_message("interviewer", f"Q{i}", "Python", {"expected_elements": []})
            await orchestrator.process_response(interview_session, f"Answer {i}", mock_config)

        # Verify all were processed
        assert len(interview_session.evaluations) == 5
        assert interview_session.questions_asked == 5

    @pytest.mark.asyncio
    async def test_long_conversation_history(self, mock_llm_client, mock_logger, large_conversation_history, candidate_profile, job_requirements, sample_topics, mock_config):
        """Test handling session with long conversation history."""
        from src.models.session import InterviewSession

        # Create session with large history
        session = InterviewSession(
            session_id="test-long",
            candidate_profile=candidate_profile,
            job_requirements=job_requirements,
            topics=sample_topics,
            current_topic="Python",
            status=SessionStatus.ACTIVE,
            start_time=datetime.now()
        )

        # Add large history
        session.conversation_history = large_conversation_history

        mock_llm_client.generate_structured = AsyncMock(return_value={
            "question": "Question",
            "reasoning": "Reason",
            "expected_elements": []
        })

        orchestrator = OrchestratorAgent(mock_llm_client, mock_logger)

        # Should handle large history gracefully
        result = await orchestrator.generate_first_question(session)

        assert result is not None
        assert "question" in result


# ============================================================================
# Edge Case Integration Tests
# ============================================================================

class TestEdgeCaseIntegration:
    """Test edge cases in multi-agent scenarios."""

    @pytest.mark.asyncio
    async def test_all_topics_exhausted(self, mock_llm_client, mock_logger, interview_session, mock_config):
        """Test behavior when all topics are exhausted."""
        # Mark all topics as covered
        for topic in interview_session.topics:
            topic.covered = True

        mock_llm_client.generate_structured = AsyncMock(return_value={
            "technical_accuracy": 4.0,
            "depth": 4.0,
            "clarity": 4.0,
            "relevance": 4.0,
            "strengths": [],
            "gaps": [],
            "feedback": "Good"
        })

        orchestrator = OrchestratorAgent(mock_llm_client, mock_logger)

        interview_session.add_message("interviewer", "Last question", interview_session.topics[-1].name, {"expected_elements": []})

        # Process final response
        result = await orchestrator.process_response(interview_session, "Final answer", mock_config)

        # Should indicate interview is complete
        assert result["interview_complete"] == True

    @pytest.mark.asyncio
    async def test_single_topic_interview(self, mock_llm_client, mock_logger, candidate_profile, job_requirements, mock_config):
        """Test interview with only one topic."""
        from src.models.candidate import Topic

        single_topic = [Topic(name="Python", priority=5, depth="surface")]

        mock_llm_client.generate_structured = AsyncMock(side_effect=[
            {"question": "Q1", "reasoning": "R", "expected_elements": []},
            {"technical_accuracy": 4.0, "depth": 4.0, "clarity": 4.0, "relevance": 4.0,
             "strengths": [], "gaps": [], "feedback": "Good"},
            {"question": "Q2", "reasoning": "R", "expected_elements": []},
            {"technical_accuracy": 4.0, "depth": 4.0, "clarity": 4.0, "relevance": 4.0,
             "strengths": [], "gaps": [], "feedback": "Good"},
        ])

        orchestrator = OrchestratorAgent(mock_llm_client, mock_logger)

        session = orchestrator.create_session(candidate_profile, job_requirements, single_topic)

        # Should handle single topic gracefully
        await orchestrator.generate_first_question(session)
        session.add_message("interviewer", "Q1", "Python", {"expected_elements": []})
        result1 = await orchestrator.process_response(session, "A1", mock_config)

        assert result1 is not None
        # No transition should occur (only one topic)
        assert not result1.get("transitioned", False)
