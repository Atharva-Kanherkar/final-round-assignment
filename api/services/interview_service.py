"""Service layer for interview operations integrating with agent system."""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from src.agents.orchestrator import OrchestratorAgent
from src.services.parser import ResumeParser, JobDescriptionParser, TopicGenerator
from src.services.llm_client import LLMClient
from src.models.session import InterviewSession as AgentSession, SessionStatus as AgentSessionStatus
from src.models.candidate import CandidateProfile, JobRequirements, Topic
from src.utils.exceptions import InvalidResumeError, InvalidJobDescriptionError

from api.models.db_models import DBSession, DBMessage, DBEvaluation, DBFinalReport, SessionStatus
from api.schemas import QuestionResponse, EvaluationResponse


class InterviewService:
    """Service for managing interview operations."""

    def __init__(
        self,
        llm_client: LLMClient,
        logger: logging.Logger,
        db: Session
    ):
        """
        Initialize interview service.

        Args:
            llm_client: LLM client instance
            logger: Logger instance
            db: Database session
        """
        self.llm_client = llm_client
        self.logger = logger
        self.db = db

        # Initialize orchestrator
        self.orchestrator = OrchestratorAgent(llm_client, logger)

        # Initialize parsers
        self.resume_parser = ResumeParser(logger)
        self.jd_parser = JobDescriptionParser(logger)
        self.topic_generator = TopicGenerator(logger)

        # In-memory session storage (active sessions)
        self.active_sessions: Dict[UUID, AgentSession] = {}

    async def create_session(
        self,
        resume_text: str,
        job_description_text: str
    ) -> tuple[DBSession, QuestionResponse]:
        """
        Create new interview session.

        Args:
            resume_text: Candidate's resume
            job_description_text: Job description

        Returns:
            Tuple of (DB session, first question)

        Raises:
            InvalidResumeError: If resume is invalid
            InvalidJobDescriptionError: If job description is invalid
        """
        self.logger.info("Creating new interview session")

        # Parse inputs
        candidate_profile = self.resume_parser.parse(resume_text)
        job_requirements = self.jd_parser.parse(job_description_text)
        topics = self.topic_generator.generate_topics(
            candidate_profile,
            job_requirements,
            max_topics=5
        )

        # Create agent session
        agent_session = self.orchestrator.create_session(
            candidate_profile,
            job_requirements,
            topics
        )

        # Store in memory
        session_uuid = UUID(agent_session.session_id)
        self.active_sessions[session_uuid] = agent_session

        # Create database record
        db_session = DBSession(
            id=session_uuid,
            candidate_name=candidate_profile.name,
            job_title=job_requirements.title,
            company=job_requirements.company,
            candidate_profile=candidate_profile.to_dict(),
            job_requirements=job_requirements.to_dict(),
            topics=[t.to_dict() for t in topics],
            current_topic=agent_session.current_topic,
            current_topic_index=0,
            status=SessionStatus.ACTIVE,
            start_time=agent_session.start_time,
            questions_asked=0
        )

        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)

        # Generate first question
        first_question_data = await self.orchestrator.generate_first_question(agent_session)

        # Save question message to database
        self._save_message(
            session_uuid,
            "interviewer",
            first_question_data["question"],
            agent_session.current_topic,
            {"expected_elements": first_question_data["expected_elements"]}
        )

        # Update session
        db_session.questions_asked = agent_session.questions_asked
        self.db.commit()

        # Prepare response
        question_response = QuestionResponse(
            question=first_question_data["question"],
            topic=agent_session.current_topic,
            question_number=1,
            topic_progress=f"{agent_session.current_topic_index + 1}/{len(topics)}",
            questions_in_topic=1
        )

        return db_session, question_response

    async def process_response(
        self,
        session_id: UUID,
        response_text: str,
        config: Dict[str, Any]
    ) -> EvaluationResponse:
        """
        Process candidate response.

        Args:
            session_id: Session ID
            response_text: Candidate's response
            config: Configuration dict

        Returns:
            EvaluationResponse with evaluation and next question

        Raises:
            ValueError: If session not found
        """
        # Get agent session from memory
        agent_session = self.active_sessions.get(session_id)
        if not agent_session:
            raise ValueError(f"Session {session_id} not found in active sessions")

        # Save candidate message
        self._save_message(session_id, "candidate", response_text, agent_session.current_topic)

        # Process through orchestrator
        result = await self.orchestrator.process_response(
            agent_session,
            response_text,
            config
        )

        # Save evaluation to database
        eval_obj = result["evaluation"]
        db_eval = DBEvaluation(
            session_id=session_id,
            question=eval_obj.question,
            response=eval_obj.response,
            topic=eval_obj.topic,
            technical_accuracy=eval_obj.technical_accuracy,
            depth=eval_obj.depth,
            clarity=eval_obj.clarity,
            relevance=eval_obj.relevance,
            overall_score=eval_obj.overall_score,
            strengths=eval_obj.strengths,
            gaps=eval_obj.gaps,
            feedback=eval_obj.feedback,
            timestamp=eval_obj.timestamp
        )
        self.db.add(db_eval)

        # Update session in database
        db_session = self.db.query(DBSession).filter(DBSession.id == session_id).first()
        if db_session:
            db_session.current_topic = agent_session.current_topic
            db_session.current_topic_index = agent_session.current_topic_index
            db_session.questions_asked = agent_session.questions_asked
            db_session.average_score = agent_session.get_average_score()
            db_session.topics = [t.to_dict() for t in agent_session.topics]

        self.db.commit()

        # Prepare response
        next_q = None
        if result.get("next_question") and not result.get("interview_complete"):
            next_q = QuestionResponse(
                question=result["next_question"]["question"],
                topic=agent_session.current_topic,
                question_number=agent_session.questions_asked,
                topic_progress=f"{agent_session.current_topic_index + 1}/{len(agent_session.topics)}",
                questions_in_topic=agent_session.get_current_topic().questions_asked if agent_session.get_current_topic() else 0
            )

        # Convert evaluation to schema
        from api.schemas import EvaluationSchema
        eval_schema = EvaluationSchema(
            id=db_eval.id,
            question=eval_obj.question,
            response=eval_obj.response,
            topic=eval_obj.topic,
            technical_accuracy=eval_obj.technical_accuracy,
            depth=eval_obj.depth,
            clarity=eval_obj.clarity,
            relevance=eval_obj.relevance,
            overall_score=eval_obj.overall_score,
            strengths=eval_obj.strengths,
            gaps=eval_obj.gaps,
            feedback=eval_obj.feedback,
            timestamp=eval_obj.timestamp
        )

        return EvaluationResponse(
            evaluation=eval_schema,
            next_question=next_q,
            transitioned=result.get("transitioned", False),
            transition_reasoning=result.get("transition_reasoning"),
            interview_complete=result.get("interview_complete", False)
        )

    async def generate_final_report(self, session_id: UUID) -> DBFinalReport:
        """
        Generate final interview report.

        Args:
            session_id: Session ID

        Returns:
            Final report database object
        """
        # Get agent session
        agent_session = self.active_sessions.get(session_id)
        if not agent_session:
            raise ValueError(f"Session {session_id} not found")

        # Generate report through orchestrator
        final_report = await self.orchestrator.generate_final_report(agent_session)

        # Update database session
        db_session = self.db.query(DBSession).filter(DBSession.id == session_id).first()
        if db_session:
            db_session.status = SessionStatus.COMPLETED
            db_session.end_time = agent_session.end_time
            db_session.average_score = final_report.overall_score

        # Create final report in database
        db_report = DBFinalReport(
            session_id=session_id,
            candidate_name=final_report.candidate_name,
            job_title=final_report.job_title,
            duration_minutes=final_report.duration_minutes,
            total_questions=final_report.total_questions,
            topics_covered=final_report.topics_covered,
            overall_score=final_report.overall_score,
            topic_summaries=[{
                "topic": ts.topic,
                "questions_count": ts.questions_count,
                "average_score": ts.average_score,
                "strengths": ts.strengths,
                "areas_for_improvement": ts.areas_for_improvement
            } for ts in final_report.topic_summaries],
            overall_strengths=final_report.overall_strengths,
            areas_for_improvement=final_report.areas_for_improvement,
            recommendation=final_report.recommendation,
            additional_notes=final_report.additional_notes
        )

        self.db.add(db_report)
        self.db.commit()
        self.db.refresh(db_report)

        # Remove from active sessions
        self.active_sessions.pop(session_id, None)

        return db_report

    def get_session(self, session_id: UUID) -> Optional[DBSession]:
        """Get session from database."""
        return self.db.query(DBSession).filter(DBSession.id == session_id).first()

    def list_sessions(self, limit: int = 50, offset: int = 0) -> List[DBSession]:
        """List all sessions."""
        return self.db.query(DBSession).order_by(DBSession.created_at.desc()).limit(limit).offset(offset).all()

    def _save_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        topic: str,
        metadata: Optional[Dict] = None
    ) -> DBMessage:
        """Save message to database."""
        message = DBMessage(
            session_id=session_id,
            role=role,
            content=content,
            topic=topic,
            metadata=metadata or {},
            timestamp=datetime.utcnow()
        )
        self.db.add(message)
        self.db.commit()
        return message
