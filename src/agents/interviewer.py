"""Interviewer agent for generating contextual questions."""
import json
from typing import Dict, Any, Optional
from .base import BaseAgent


class InterviewerAgent(BaseAgent):
    """Agent responsible for generating contextual interview questions."""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate the next interview question.

        Context should include:
            - candidate_profile: CandidateProfile object
            - job_requirements: JobRequirements object
            - current_topic: str
            - topic_depth: str ("surface" | "deep")
            - conversation_history: List[Message]
            - last_evaluation: Optional[ResponseEvaluation]

        Returns:
            {
                "question": str,
                "reasoning": str,
                "expected_elements": List[str]
            }
        """
        self.logger.info(f"📝 InterviewerAgent: Generating question for topic: {context.get('current_topic')}")

        try:
            # Build prompt
            prompt = self._build_prompt(context)
            self.logger.info(f"📝 InterviewerAgent: Prompt built, calling LLM...")

            # Call LLM
            response = await self.llm.generate_structured(
                prompt=prompt,
                system_message="You are an expert technical interviewer conducting a professional interview.",
                response_format={
                    "question": "string",
                    "reasoning": "string",
                    "expected_elements": "array of strings"
                }
            )
            self.logger.info(f"📝 InterviewerAgent: Question generated successfully")

            result = {
                "question": response.get("question", ""),
                "reasoning": response.get("reasoning", ""),
                "expected_elements": response.get("expected_elements", [])
            }

            self._log_execution(context, result)
            return result

        except Exception as e:
            self.logger.error(f"Error generating question: {str(e)}")
            # Return fallback question
            return self._fallback_question(context)

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """Build the prompt for question generation."""
        candidate = context.get("candidate_profile")
        job = context.get("job_requirements")
        topic = context.get("current_topic")
        depth = context.get("topic_depth", "surface")
        history = context.get("conversation_history", [])
        last_eval = context.get("last_evaluation")

        # Get recent conversation context
        recent_exchanges = []
        if history:
            recent = history[-4:]  # Last 2 Q&A pairs
            for msg in recent:
                recent_exchanges.append(f"{msg.role}: {msg.content}")

        recent_context = "\n".join(recent_exchanges) if recent_exchanges else "No previous questions"

        # Build evaluation context
        eval_context = ""
        if last_eval:
            eval_context = f"""
Previous Response Evaluation:
- Score: {last_eval.overall_score}/5.0
- Strengths: {', '.join(last_eval.strengths)}
- Gaps: {', '.join(last_eval.gaps)}
"""

        prompt = f"""You are conducting a technical interview for the position of {job.title} at {job.company}.

Candidate Background:
- Name: {candidate.name}
- Experience: {candidate.experience_years} years
- Skills: {', '.join(candidate.skills)}
- Education: {candidate.education}

Job Requirements:
- Required Skills: {', '.join(job.required_skills)}
- Responsibilities: {', '.join(job.responsibilities[:3])}

Current Topic: {topic}
Topic Depth: {depth} (surface = introductory/conceptual, deep = implementation/architecture/edge cases)

Recent Conversation:
{recent_context}
{eval_context}

Generate the next interview question that:
1. Probes the candidate's understanding of {topic} at {depth} level
2. Builds naturally from the previous conversation
3. Tests practical application relevant to this role
4. Is appropriate for someone with {candidate.experience_years} years of experience
5. {"Explores fundamental concepts and use cases" if depth == "surface" else "Dives into implementation details, trade-offs, and edge cases"}

Return your response as JSON with:
- "question": The interview question to ask
- "reasoning": Why this question is relevant (1 sentence)
- "expected_elements": List of 3-5 key points a strong answer should cover
"""

        return prompt

    def _fallback_question(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return a fallback question if LLM fails."""
        topic = context.get("current_topic", "general experience")
        return {
            "question": f"Can you describe your experience with {topic} and how you've applied it in your previous roles?",
            "reasoning": "Fallback question due to API error",
            "expected_elements": ["Past experience", "Specific examples", "Outcomes"]
        }
