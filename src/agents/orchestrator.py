"""Orchestrator agent for coordinating the interview flow."""
import json
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from .base import BaseAgent
from .interviewer import InterviewerAgent
from .evaluator import EvaluatorAgent
from .topic_manager import TopicManagerAgent
from ..models.session import InterviewSession, SessionStatus
from ..models.evaluation import FinalReport, TopicSummary


class OrchestratorAgent(BaseAgent):
    """Master agent that coordinates all other agents and manages interview lifecycle."""

    def __init__(self, llm_client: Any, logger: Any):
        """Initialize orchestrator with sub-agents."""
        super().__init__(llm_client, logger)

        # Initialize sub-agents
        self.interviewer = InterviewerAgent(llm_client, logger)
        self.evaluator = EvaluatorAgent(llm_client, logger)
        self.topic_manager = TopicManagerAgent(llm_client, logger)

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main orchestration logic - not used directly.
        Use specific methods instead: start_interview, process_response, etc.
        """
        pass

    def create_session(
        self,
        candidate_profile: Any,
        job_requirements: Any,
        topics: list
    ) -> InterviewSession:
        """
        Create a new interview session.

        Args:
            candidate_profile: CandidateProfile object
            job_requirements: JobRequirements object
            topics: List of Topic objects

        Returns:
            InterviewSession object
        """
        session = InterviewSession(
            session_id=str(uuid.uuid4()),
            candidate_profile=candidate_profile,
            job_requirements=job_requirements,
            topics=topics,
            current_topic=topics[0].name if topics else "General",
            current_topic_index=0,
            status=SessionStatus.ACTIVE,
            start_time=datetime.now()
        )

        self.logger.info(
            f"Created interview session {session.session_id} for {candidate_profile.name}"
        )

        return session

    async def generate_first_question(self, session: InterviewSession) -> Dict[str, Any]:
        """
        Generate the first question of the interview.

        Args:
            session: InterviewSession object

        Returns:
            Dictionary with question details
        """
        self.logger.info("Generating first interview question")

        context = {
            "candidate_profile": session.candidate_profile,
            "job_requirements": session.job_requirements,
            "current_topic": session.current_topic,
            "topic_depth": "surface",
            "conversation_history": [],
            "last_evaluation": None
        }

        result = await self.interviewer.execute(context)

        # Add to conversation history
        session.add_message(
            role="interviewer",
            content=result["question"],
            topic=session.current_topic,
            metadata={"expected_elements": result["expected_elements"]}
        )

        return result

    async def process_response(
        self,
        session: InterviewSession,
        candidate_response: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process candidate response and generate next question or transition.

        Args:
            session: InterviewSession object
            candidate_response: The candidate's answer
            config: Configuration dict with min/max questions per topic

        Returns:
            Dictionary with evaluation, next question, and transition info
        """
        self.logger.info(f"Processing response for topic: {session.current_topic}")

        # Add candidate response to history
        session.add_message(
            role="candidate",
            content=candidate_response,
            topic=session.current_topic
        )

        # Step 1: Evaluate the response
        last_question_msg = [m for m in session.conversation_history if m.role == "interviewer"][-1]
        eval_context = {
            "question": last_question_msg.content,
            "response": candidate_response,
            "topic": session.current_topic,
            "expected_elements": last_question_msg.metadata.get("expected_elements", []),
            "candidate_profile": session.candidate_profile
        }

        eval_result = await self.evaluator.execute(eval_context)
        evaluation = eval_result["evaluation"]
        session.add_evaluation(evaluation)

        # Step 2: Check if we should transition topics
        current_topic_obj = session.get_current_topic()
        current_topic_obj.questions_asked += 1

        topic_scores = [e.overall_score for e in session.evaluations if e.topic == session.current_topic]

        transition_context = {
            "current_topic": current_topic_obj,
            "all_topics": session.topics,
            "recent_scores": topic_scores,
            "questions_in_topic": current_topic_obj.questions_asked,
            "total_questions": session.questions_asked,
            "min_questions_per_topic": config.get("min_questions_per_topic", 2),
            "max_questions_per_topic": config.get("max_questions_per_topic", 4),
            "candidate_profile": session.candidate_profile,
            "job_requirements": session.job_requirements
        }

        transition_result = await self.topic_manager.execute(transition_context)

        # Step 3: Handle transition or continue
        next_question = None
        transitioned = False

        if transition_result["should_transition"] and transition_result["next_topic"]:
            # Mark current topic as covered
            current_topic_obj.covered = True

            # Transition to next topic
            session.current_topic = transition_result["next_topic"]
            session.current_topic_index += 1

            # Update next topic depth
            next_topic_obj = session.get_current_topic()
            if next_topic_obj:
                next_topic_obj.depth = transition_result.get("next_depth", "surface")

            transitioned = True
            self.logger.info(f"Transitioning to topic: {session.current_topic}")

        else:
            # Update depth if needed
            if transition_result.get("next_depth") and current_topic_obj:
                current_topic_obj.depth = transition_result["next_depth"]

        # Step 4: Generate next question (if interview not complete)
        if session.current_topic_index < len(session.topics):
            current_topic_obj = session.get_current_topic()

            question_context = {
                "candidate_profile": session.candidate_profile,
                "job_requirements": session.job_requirements,
                "current_topic": session.current_topic,
                "topic_depth": current_topic_obj.depth if current_topic_obj else "surface",
                "conversation_history": session.conversation_history[-6:],  # Last 3 exchanges
                "last_evaluation": evaluation
            }

            next_question = await self.interviewer.execute(question_context)

            # Add to conversation history
            session.add_message(
                role="interviewer",
                content=next_question["question"],
                topic=session.current_topic,
                metadata={"expected_elements": next_question["expected_elements"]}
            )

        return {
            "evaluation": evaluation,
            "transitioned": transitioned,
            "transition_reasoning": transition_result.get("reasoning"),
            "next_question": next_question,
            "interview_complete": session.current_topic_index >= len(session.topics)
        }

    async def generate_final_report(self, session: InterviewSession) -> FinalReport:
        """
        Generate comprehensive final evaluation report.

        Args:
            session: Completed InterviewSession

        Returns:
            FinalReport object
        """
        self.logger.info(f"Generating final report for session {session.session_id}")

        session.status = SessionStatus.COMPLETED
        session.end_time = datetime.now()

        duration = (session.end_time - session.start_time).total_seconds() / 60.0

        # Calculate topic summaries
        topic_summaries = []
        for topic in session.topics:
            if topic.covered:
                topic_evals = [e for e in session.evaluations if e.topic == topic.name]
                if topic_evals:
                    avg_score = sum(e.overall_score for e in topic_evals) / len(topic_evals)
                    all_strengths = [s for e in topic_evals for s in e.strengths]
                    all_gaps = [g for e in topic_evals for g in e.gaps]

                    summary = TopicSummary(
                        topic=topic.name,
                        questions_count=len(topic_evals),
                        average_score=avg_score,
                        strengths=all_strengths[:3],  # Top 3
                        areas_for_improvement=all_gaps[:2]  # Top 2
                    )
                    topic_summaries.append(summary)

        # Calculate overall score
        overall_score = session.get_average_score()

        # Generate recommendation
        if overall_score >= 4.0:
            recommendation = "Strong Hire"
        elif overall_score >= 3.5:
            recommendation = "Hire"
        elif overall_score >= 3.0:
            recommendation = "Maybe"
        else:
            recommendation = "No Hire"

        # Aggregate strengths and improvements
        all_strengths = [s for e in session.evaluations for s in e.strengths]
        all_gaps = [g for e in session.evaluations for g in e.gaps]

        # Use LLM to generate narrative summary
        summary_prompt = f"""Generate a brief final interview summary.

Candidate: {session.candidate_profile.name}
Position: {session.job_requirements.title}
Topics Covered: {', '.join([t.topic for t in topic_summaries])}
Overall Score: {overall_score:.1f}/5.0
Total Questions: {session.questions_asked}

Key Strengths Demonstrated:
{chr(10).join(f"- {s}" for s in all_strengths[:5])}

Areas for Improvement:
{chr(10).join(f"- {g}" for g in all_gaps[:5])}

Provide 2-3 sentences summarizing the candidate's performance and readiness for the role.
"""

        try:
            summary_response = await self.llm.generate_text(
                prompt=summary_prompt,
                system_message="You are an expert interviewer providing final feedback."
            )
            additional_notes = summary_response
        except Exception as e:
            self.logger.error(f"Error generating summary: {str(e)}")
            additional_notes = f"Candidate demonstrated {overall_score:.1f}/5.0 performance across {len(topic_summaries)} topics."

        # Create final report
        report = FinalReport(
            session_id=session.session_id,
            candidate_name=session.candidate_profile.name,
            job_title=session.job_requirements.title,
            interview_date=session.start_time,
            duration_minutes=duration,
            total_questions=session.questions_asked,
            topics_covered=[t.topic for t in topic_summaries],
            overall_score=overall_score,
            topic_summaries=topic_summaries,
            overall_strengths=list(set(all_strengths))[:5],
            areas_for_improvement=list(set(all_gaps))[:5],
            recommendation=recommendation,
            additional_notes=additional_notes
        )

        session.final_report = report
        return report
