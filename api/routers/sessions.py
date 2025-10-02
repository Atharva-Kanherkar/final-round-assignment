"""Interview session endpoints."""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import logging
import json
from datetime import datetime

from api.database import get_db
from api.schemas import (
    CreateSessionRequest,
    SubmitResponseRequest,
    SessionResponse,
    SessionDetailResponse,
    QuestionResponse,
    EvaluationResponse,
    FinalReportResponse,
    WSMessage
)
from api.services.interview_service import InterviewService
from api.models.db_models import DBSession, DBMessage, DBEvaluation, DBFinalReport
from api.utils.file_parser import FileParser
from src.services.llm_client import LLMClient
from src.utils.config import load_config
from src.utils.logger import setup_logger

router = APIRouter()
logger = logging.getLogger(__name__)


def get_interview_service(db: Session = Depends(get_db)) -> InterviewService:
    """
    Dependency to get interview service.

    Args:
        db: Database session

    Returns:
        InterviewService instance
    """
    try:
        config = load_config()
        llm_client = LLMClient(
            api_key=config.openai_api_key,
            model_name=config.model_name,
            timeout=config.timeout_seconds,
            max_retries=config.max_retries,
            logger=logger
        )
        return InterviewService(llm_client, logger, db)
    except Exception as e:
        logger.error(f"Failed to create interview service: {e}")
        raise HTTPException(status_code=500, detail="Service initialization failed")


# ============================================================================
# Session Management Endpoints
# ============================================================================

@router.post("/sessions", response_model=dict, status_code=201)
async def create_session(
    request: CreateSessionRequest,
    service: InterviewService = Depends(get_interview_service)
):
    """
    Create new interview session with text input.

    Args:
        request: Session creation request with resume and job description

    Returns:
        Session details and first question
    """
    try:
        db_session, first_question = await service.create_session(
            request.resume_text,
            request.job_description_text
        )

        return {
            "session_id": str(db_session.id),
            "candidate_name": db_session.candidate_name,
            "job_title": db_session.job_title,
            "company": db_session.company,
            "topics": db_session.topics,
            "first_question": first_question.dict(),
            "status": db_session.status
        }

    except Exception as e:
        logger.error(f"Session creation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/upload", response_model=dict, status_code=201)
async def create_session_with_files(
    resume_file: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT)"),
    job_description_file: Optional[UploadFile] = File(None, description="Job description file (optional)"),
    job_description_text: Optional[str] = Form(None, description="Job description as text (if file not provided)"),
    service: InterviewService = Depends(get_interview_service)
):
    """
    Create new interview session with file upload.

    Args:
        resume_file: Resume file (PDF, DOCX, or TXT)
        job_description_file: Job description file (optional)
        job_description_text: Job description as text (if file not provided)

    Returns:
        Session details and first question
    """
    try:
        # Parse resume file
        logger.info(f"Parsing resume file: {resume_file.filename}")
        resume_text = await FileParser.parse_file(resume_file)

        # Parse job description (file or text)
        if job_description_file:
            logger.info(f"Parsing job description file: {job_description_file.filename}")
            jd_text = await FileParser.parse_file(job_description_file)
        elif job_description_text:
            jd_text = job_description_text.strip()
            if len(jd_text) < 50:
                raise HTTPException(
                    status_code=400,
                    detail="Job description text is too short (minimum 50 characters)"
                )
        else:
            raise HTTPException(
                status_code=400,
                detail="Either job_description_file or job_description_text must be provided"
            )

        # Create session
        db_session, first_question = await service.create_session(
            resume_text,
            jd_text
        )

        return {
            "session_id": str(db_session.id),
            "candidate_name": db_session.candidate_name,
            "job_title": db_session.job_title,
            "company": db_session.company,
            "topics": db_session.topics,
            "first_question": first_question.dict(),
            "status": db_session.status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session creation with files failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    service: InterviewService = Depends(get_interview_service)
):
    """
    List all interview sessions.

    Args:
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip

    Returns:
        List of sessions
    """
    sessions = service.list_sessions(limit=limit, offset=offset)
    return sessions


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get session details.

    Args:
        session_id: Session ID

    Returns:
        Session details
    """
    db_session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get last interviewer message as current question
    last_question = db.query(DBMessage).filter(
        DBMessage.session_id == session_id,
        DBMessage.role == "interviewer"
    ).order_by(DBMessage.timestamp.desc()).first()

    response = {
        "session_id": str(db_session.id),
        "candidate_name": db_session.candidate_name,
        "job_title": db_session.job_title,
        "company": db_session.company,
        "current_topic": db_session.current_topic,
        "status": db_session.status,
        "topics": db_session.topics,
        "questions_asked": db_session.questions_asked,
        "first_question": {
            "question": last_question.content if last_question else "",
            "topic": last_question.topic if last_question else db_session.current_topic,
            "question_number": db_session.questions_asked,
            "topic_progress": f"{db_session.current_topic_index + 1}/{len(db_session.topics)}",
            "questions_in_topic": 1
        } if last_question else None
    }

    return response


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    service: InterviewService = Depends(get_interview_service)
):
    """
    Delete interview session.

    Args:
        session_id: Session ID
    """
    db_session = service.get_session(session_id)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Remove from active sessions
    service.active_sessions.pop(session_id, None)

    # Delete from database (cascade will handle related records)
    db.delete(db_session)
    db.commit()

    return None


# ============================================================================
# Interview Interaction Endpoints
# ============================================================================

@router.post("/sessions/{session_id}/respond", response_model=EvaluationResponse)
async def submit_response(
    session_id: UUID,
    request: SubmitResponseRequest,
    service: InterviewService = Depends(get_interview_service)
):
    """
    Submit candidate response and get evaluation.

    Args:
        session_id: Session ID
        request: Response submission

    Returns:
        Evaluation and next question
    """
    try:
        # Use config from environment variables
        from src.utils.config import load_config
        cfg = load_config()
        config = {
            "min_questions_per_topic": cfg.questions_per_topic_min,
            "max_questions_per_topic": cfg.questions_per_topic_max
        }

        result = await service.process_response(
            session_id,
            request.response,
            config
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Response processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/complete", response_model=FinalReportResponse)
async def complete_session(
    session_id: UUID,
    service: InterviewService = Depends(get_interview_service)
):
    """
    Complete interview and generate final report.

    Args:
        session_id: Session ID

    Returns:
        Final interview report
    """
    try:
        final_report = await service.generate_final_report(session_id)
        return final_report

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Session completion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/messages", response_model=List[dict])
async def get_messages(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get all messages for a session.

    Args:
        session_id: Session ID

    Returns:
        List of messages
    """
    messages = db.query(DBMessage).filter(
        DBMessage.session_id == session_id
    ).order_by(DBMessage.timestamp).all()

    return [
        {
            "id": str(msg.id),
            "role": msg.role,
            "content": msg.content,
            "topic": msg.topic,
            "timestamp": msg.timestamp.isoformat()
        }
        for msg in messages
    ]


@router.get("/sessions/{session_id}/evaluations", response_model=List[dict])
async def get_evaluations(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get all evaluations for a session.

    Args:
        session_id: Session ID

    Returns:
        List of evaluations
    """
    evaluations = db.query(DBEvaluation).filter(
        DBEvaluation.session_id == session_id
    ).order_by(DBEvaluation.timestamp).all()

    return [
        {
            "id": str(eval.id),
            "question": eval.question,
            "response": eval.response,
            "topic": eval.topic,
            "overall_score": eval.overall_score,
            "scores": {
                "technical_accuracy": eval.technical_accuracy,
                "depth": eval.depth,
                "clarity": eval.clarity,
                "relevance": eval.relevance
            },
            "strengths": eval.strengths,
            "gaps": eval.gaps,
            "feedback": eval.feedback,
            "timestamp": eval.timestamp.isoformat()
        }
        for eval in evaluations
    ]


# ============================================================================
# WebSocket Endpoint for Real-time Interview
# ============================================================================

@router.websocket("/ws/interview/{session_id}")
async def interview_websocket(
    websocket: WebSocket,
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time interview interaction.

    Protocol:
        Client → Server: {"type": "response", "data": {"response": "answer text"}}
        Server → Client: {"type": "evaluation", "data": {...}}
        Server → Client: {"type": "question", "data": {...}}
        Server → Client: {"type": "status", "data": {...}}
        Server → Client: {"type": "complete", "data": {...}}
        Server → Client: {"type": "error", "data": {...}}
    """
    await websocket.accept()

    try:
        # Get service
        from src.utils.config import load_config
        config = load_config()
        llm_client = LLMClient(
            api_key=config.openai_api_key,
            model_name=config.model_name,
            logger=logger
        )
        service = InterviewService(llm_client, logger, db)

        # Verify session exists
        db_session = service.get_session(session_id)
        if not db_session:
            await websocket.send_json({
                "type": "error",
                "data": {"error": "Session not found", "recoverable": False}
            })
            await websocket.close()
            return

        # Send current question if exists
        messages = db.query(DBMessage).filter(
            DBMessage.session_id == session_id,
            DBMessage.role == "interviewer"
        ).order_by(DBMessage.timestamp.desc()).first()

        if messages:
            await websocket.send_json({
                "type": "question",
                "data": {
                    "question": messages.content,
                    "topic": messages.topic,
                    "question_number": db_session.questions_asked
                }
            })

        # Message loop
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            if data.get("type") == "response":
                # Process response
                response_text = data.get("data", {}).get("response", "")

                if not response_text or response_text.strip().lower() == "exit":
                    # End interview
                    await websocket.send_json({
                        "type": "complete",
                        "data": {"reason": "User ended interview"}
                    })
                    break

                try:
                    # Process through service with config from environment
                    from src.utils.config import load_config
                    cfg = load_config()
                    result = await service.process_response(
                        session_id,
                        response_text,
                        {
                            "min_questions_per_topic": cfg.questions_per_topic_min,
                            "max_questions_per_topic": cfg.questions_per_topic_max
                        }
                    )

                    # Send evaluation
                    await websocket.send_json({
                        "type": "evaluation",
                        "data": {
                            "overall_score": result.evaluation.overall_score,
                            "scores": {
                                "technical_accuracy": result.evaluation.technical_accuracy,
                                "depth": result.evaluation.depth,
                                "clarity": result.evaluation.clarity,
                                "relevance": result.evaluation.relevance
                            },
                            "strengths": result.evaluation.strengths,
                            "gaps": result.evaluation.gaps,
                            "feedback": result.evaluation.feedback
                        }
                    })

                    # Check if complete
                    if result.interview_complete:
                        # Generate final report
                        final_report = await service.generate_final_report(session_id)

                        await websocket.send_json({
                            "type": "complete",
                            "data": {
                                "overall_score": final_report.overall_score,
                                "recommendation": final_report.recommendation,
                                "topics_covered": final_report.topics_covered
                            }
                        })
                        break

                    # Send next question
                    if result.next_question:
                        await websocket.send_json({
                            "type": "question",
                            "data": {
                                "question": result.next_question.question,
                                "topic": result.next_question.topic,
                                "question_number": result.next_question.question_number
                            }
                        })

                        # Send topic transition if occurred
                        if result.transitioned:
                            await websocket.send_json({
                                "type": "status",
                                "data": {
                                    "event": "topic_transition",
                                    "reasoning": result.transition_reasoning
                                }
                            })

                except Exception as e:
                    logger.error(f"Error processing response: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "data": {
                            "error": str(e),
                            "recoverable": True
                        }
                    })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"error": str(e), "recoverable": False}
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
