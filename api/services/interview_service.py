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
            status="active",
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
        # Get agent session from memory, or reconstruct from database
        agent_session = self.active_sessions.get(session_id)
        if not agent_session:
            self.logger.info(f"Session {session_id} not in memory, reconstructing from database")
            agent_session = self._reconstruct_session_from_db(session_id)
            self.active_sessions[session_id] = agent_session

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
            db_session.status = "completed"
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
            msg_metadata=metadata or {},  # Changed from metadata to msg_metadata
            timestamp=datetime.utcnow()
        )
        self.db.add(message)
        self.db.commit()
        return message

    def _reconstruct_session_from_db(self, session_id: UUID) -> AgentSession:
        """
        Reconstruct agent session from database.

        Args:
            session_id: Session ID

        Returns:
            Reconstructed AgentSession

        Raises:
            ValueError: If session not found
        """
        # Load database session
        db_session = self.db.query(DBSession).filter(DBSession.id == session_id).first()
        if not db_session:
            raise ValueError(f"Session {session_id} not found in database")

        # Reconstruct candidate profile
        candidate_data = db_session.candidate_profile
        candidate_profile = CandidateProfile(
            name=candidate_data['name'],
            skills=candidate_data['skills'],
            experience_years=candidate_data['experience_years'],
            education=candidate_data['education'],
            past_roles=candidate_data['past_roles'],
            summary=candidate_data.get('summary', ''),
            raw_resume=candidate_data.get('raw_resume', '')
        )

        # Reconstruct job requirements
        job_data = db_session.job_requirements
        job_requirements = JobRequirements(
            title=job_data['title'],
            company=job_data['company'],
            required_skills=job_data['required_skills'],
            preferred_skills=job_data.get('preferred_skills', []),
            responsibilities=job_data.get('responsibilities', []),
            experience_required=job_data.get('experience_required', 0),
            raw_description=job_data.get('raw_description', '')
        )

        # Reconstruct topics
        topics = [
            Topic(
                name=t['name'],
                priority=t['priority'],
                depth=t.get('depth', 'surface'),
                questions_asked=t.get('questions_asked', 0),
                covered=t.get('covered', False)
            )
            for t in db_session.topics
        ]

        # Create agent session
        from src.models.session import SessionStatus as AgentSessionStatus
        agent_session = AgentSession(
            session_id=str(session_id),
            candidate_profile=candidate_profile,
            job_requirements=job_requirements,
            topics=topics,
            current_topic=db_session.current_topic,
            current_topic_index=db_session.current_topic_index,
            status=AgentSessionStatus.ACTIVE if db_session.status == "active" else AgentSessionStatus.COMPLETED,
            start_time=db_session.start_time,
            end_time=db_session.end_time,
            questions_asked=db_session.questions_asked
        )

        # Load messages from database and reconstruct conversation history
        db_messages = self.db.query(DBMessage).filter(
            DBMessage.session_id == session_id
        ).order_by(DBMessage.timestamp).all()

        from src.models.session import Message
        for db_msg in db_messages:
            msg = Message(
                role=db_msg.role,
                content=db_msg.content,
                timestamp=db_msg.timestamp,
                topic=db_msg.topic,
                metadata=db_msg.msg_metadata or {}
            )
            agent_session.conversation_history.append(msg)

        # Load evaluations from database
        db_evals = self.db.query(DBEvaluation).filter(
            DBEvaluation.session_id == session_id
        ).order_by(DBEvaluation.timestamp).all()

        from src.models.evaluation import ResponseEvaluation
        for db_eval in db_evals:
            evaluation = ResponseEvaluation(
                question=db_eval.question,
                response=db_eval.response,
                topic=db_eval.topic,
                timestamp=db_eval.timestamp,
                technical_accuracy=db_eval.technical_accuracy,
                depth=db_eval.depth,
                clarity=db_eval.clarity,
                relevance=db_eval.relevance,
                overall_score=db_eval.overall_score,
                strengths=db_eval.strengths or [],
                gaps=db_eval.gaps or [],
                feedback=db_eval.feedback
            )
            agent_session.evaluations.append(evaluation)

        self.logger.info(f"Reconstructed session {session_id} with {len(db_messages)} messages and {len(db_evals)} evaluations")

        return agent_session
