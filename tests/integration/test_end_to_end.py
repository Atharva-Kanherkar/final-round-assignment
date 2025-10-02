"""
End-to-end integration tests.

Tests complete interview scenarios from file input to final report.
"""
import pytest
import os
import tempfile
from unittest.mock import AsyncMock, patch
from pathlib import Path

from src.services.parser import ResumeParser, JobDescriptionParser, TopicGenerator
from src.agents.orchestrator import OrchestratorAgent
from src.models.session import SessionStatus


# ============================================================================
# End-to-End Interview Tests
# ============================================================================

class TestEndToEndInterview:
    """Test complete interview flows."""

    @pytest.mark.asyncio
    async def test_full_interview_cycle(self, mock_llm_client, mock_logger, valid_resume_text, valid_job_description_text):
        """Test complete interview from parsing to final report."""
        # Parse inputs
        resume_parser = ResumeParser(mock_logger)
        jd_parser = JobDescriptionParser(mock_logger)
        topic_gen = TopicGenerator(mock_logger)

        candidate = resume_parser.parse(valid_resume_text)
        job = jd_parser.parse(valid_job_description_text)
        topics = topic_gen.generate_topics(candidate, job, max_topics=3)

        # Setup mock responses for full interview
        mock_responses = []
        for i in range(20):  # Enough for full interview
            if i % 2 == 0:
                # Question or evaluation
                mock_responses.append({
                    "question": f"Question {i//2 + 1}",
                    "reasoning": "Test",
                    "expected_elements": ["Element"]
                })
            else:
                # Evaluation
                mock_responses.append({
                    "technical_accuracy": 4.0,
                    "depth": 3.5,
                    "clarity": 4.0,
                    "relevance": 4.0,
                    "strengths": ["Good answer"],
                    "gaps": [],
                    "feedback": "Well done"
                })

        # Add final report summary response
        mock_responses.append("Candidate demonstrated strong technical skills across all topics.")

        mock_llm_client.generate_structured = AsyncMock(side_effect=mock_responses)
        mock_llm_client.generate_text = AsyncMock(return_value="Candidate performed well overall.")

        # Create interview session
        orchestrator = OrchestratorAgent(mock_llm_client, mock_logger)
        session = orchestrator.create_session(candidate, job, topics)

        # Run interview
        await orchestrator.generate_first_question(session)

        config = {"min_questions_per_topic": 1, "max_questions_per_topic": 2}

        # Process several responses
        for i in range(6):
            session.add_message("candidate", f"Answer {i}", session.current_topic)
            result = await orchestrator.process_response(session, f"Answer {i}", config)

            if result["interview_complete"]:
                break

        # Generate final report
        final_report = await orchestrator.generate_final_report(session)

        # Verify report
        assert final_report is not None
        assert final_report.session_id == session.session_id
        assert final_report.candidate_name == candidate.name
        assert final_report.job_title == job.title
        assert final_report.total_questions > 0
        assert len(final_report.topics_covered) > 0
        assert final_report.overall_score >= 0 and final_report.overall_score <= 5
        assert final_report.recommendation in ["Strong Hire", "Hire", "Maybe", "No Hire"]

    @pytest.mark.asyncio
    async def test_interview_with_early_termination(self, mock_llm_client, mock_logger, candidate_profile, job_requirements, sample_topics):
        """Test interview terminated early."""
        mock_llm_client.generate_structured = AsyncMock(side_effect=[
            {"question": "Q1", "reasoning": "R", "expected_elements": []},
            {"technical_accuracy": 4.0, "depth": 4.0, "clarity": 4.0, "relevance": 4.0,
             "strengths": [], "gaps": [], "feedback": "Good"},
        ])
        mock_llm_client.generate_text = AsyncMock(return_value="Interview ended early.")

        orchestrator = OrchestratorAgent(mock_llm_client, mock_logger)
        session = orchestrator.create_session(candidate_profile, job_requirements, sample_topics)

        # Answer only 1 question, then generate report
        await orchestrator.generate_first_question(session)
        session.add_message("candidate", "Answer", "Python")

        # Generate final report early
        final_report = await orchestrator.generate_final_report(session)

        assert final_report is not None
        assert session.status == SessionStatus.COMPLETED
        assert session.end_time is not None


# ============================================================================
# File I/O Integration Tests
# ============================================================================

class TestFileIOIntegration:
    """Test file reading and session saving."""

    def test_parse_from_file(self, mock_logger):
        """Test parsing resume from actual file."""
        parser = ResumeParser(mock_logger)

        resume_path = Path("data/sample_resume.txt")
        if resume_path.exists():
            with open(resume_path, 'r') as f:
                resume_text = f.read()

            profile = parser.parse(resume_text)

            assert profile.name is not None
            assert len(profile.skills) > 0

    def test_session_serialization(self, interview_session):
        """Test session can be serialized to dict."""
        session_dict = interview_session.to_dict()

        assert session_dict["session_id"] == interview_session.session_id
        assert session_dict["current_topic"] == interview_session.current_topic
        assert "candidate_profile" in session_dict
        assert "job_requirements" in session_dict
        assert "topics" in session_dict

    @pytest.mark.asyncio
    async def test_session_save_and_metadata(self, mock_llm_client, mock_logger, candidate_profile, job_requirements, sample_topics):
        """Test session can be saved with all metadata."""
        orchestrator = OrchestratorAgent(mock_llm_client, mock_logger)
        session = orchestrator.create_session(candidate_profile, job_requirements, sample_topics)

        # Add some data
        session.add_message("interviewer", "Question", "Python", {})
        session.add_message("candidate", "Answer", "Python")

        # Serialize
        session_dict = session.to_dict()

        # Verify all data preserved
        assert len(session_dict["conversation_history"]) == 2
        assert session_dict["questions_asked"] == 1
        assert session_dict["current_topic"] == "Python"


# ============================================================================
# Error Recovery Integration Tests
# ============================================================================

class TestErrorRecoveryIntegration:
    """Test error recovery across components."""

    @pytest.mark.asyncio
    async def test_recovery_from_transient_failures(self, mock_llm_client, mock_logger, interview_session, mock_config):
        """Test system recovers from transient failures."""
        # Fail twice, then succeed
        call_count = 0

        def side_effect_generator(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Transient error")
            return {
                "question": "Question after recovery",
                "reasoning": "Recovered",
                "expected_elements": []
            }

        mock_llm_client.generate_structured = AsyncMock(side_effect=side_effect_generator)

        orchestrator = OrchestratorAgent(mock_llm_client, mock_logger)

        # Should recover and eventually succeed
        result = await orchestrator.generate_first_question(interview_session)

        # Either got fallback or recovered
        assert result is not None
        assert "question" in result

    @pytest.mark.asyncio
    async def test_partial_agent_failures(self, mock_llm_client, mock_logger, interview_session, mock_config):
        """Test system continues when some agents fail."""
        # Evaluator fails, but next question still generated
        mock_llm_client.generate_structured = AsyncMock(side_effect=[
            Exception("Evaluator failed"),  # Evaluation fails
            {  # But next question succeeds
                "question": "Next question despite evaluation failure",
                "reasoning": "Continue",
                "expected_elements": []
            }
        ])

        orchestrator = OrchestratorAgent(mock_llm_client, mock_logger)

        interview_session.add_message("interviewer", "Test?", "Python", {"expected_elements": []})

        result = await orchestrator.process_response(interview_session, "Answer", mock_config)

        # Should have fallback evaluation
        assert result["evaluation"] is not None
        # Should still generate next question
        assert result["next_question"] is not None or result["interview_complete"]
