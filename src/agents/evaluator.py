"""Evaluator agent for assessing candidate responses."""
import json
from typing import Dict, Any
from datetime import datetime
from .base import BaseAgent
from ..models.evaluation import ResponseEvaluation


class EvaluatorAgent(BaseAgent):
    """Agent responsible for evaluating candidate responses."""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a candidate's response.

        Context should include:
            - question: str
            - response: str
            - topic: str
            - expected_elements: List[str]
            - candidate_profile: CandidateProfile

        Returns:
            ResponseEvaluation object as dict
        """
        question = context.get("question")
        response = context.get("response")
        topic = context.get("topic")

        self.logger.info(f"⭐ EvaluatorAgent: Evaluating response for topic: {topic}")

        try:
            # Build prompt
            prompt = self._build_prompt(context)
            self.logger.info(f"⭐ EvaluatorAgent: Prompt built, calling LLM...")

            # Call LLM
            eval_response = await self.llm.generate_structured(
                prompt=prompt,
                system_message="You are an expert technical interviewer providing constructive feedback.",
                response_format={
                    "technical_accuracy": "float 0-5",
                    "depth": "float 0-5",
                    "clarity": "float 0-5",
                    "relevance": "float 0-5",
                    "strengths": "array of strings",
                    "gaps": "array of strings",
                    "feedback": "string"
                }
            )
            self.logger.info(f"⭐ EvaluatorAgent: Evaluation complete")

            # Calculate overall score
            overall_score = (
                eval_response["technical_accuracy"] +
                eval_response["depth"] +
                eval_response["clarity"] +
                eval_response["relevance"]
            ) / 4.0

            # Create evaluation object
            evaluation = ResponseEvaluation(
                question=question,
                response=response,
                topic=topic,
                timestamp=datetime.now(),
                technical_accuracy=eval_response["technical_accuracy"],
                depth=eval_response["depth"],
                clarity=eval_response["clarity"],
                relevance=eval_response["relevance"],
                overall_score=overall_score,
                strengths=eval_response["strengths"],
                gaps=eval_response["gaps"],
                feedback=eval_response["feedback"]
            )

            result = {"evaluation": evaluation}
            self._log_execution(context, {"overall_score": overall_score})
            return result

        except Exception as e:
            self.logger.error(f"Error evaluating response: {str(e)}")
            return self._fallback_evaluation(context)

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """Build the evaluation prompt."""
        question = context.get("question")
        response = context.get("response")
        expected = context.get("expected_elements", [])
        candidate = context.get("candidate_profile")

        prompt = f"""Evaluate the following interview response:

Question: {question}

Candidate's Response:
{response}

Expected Key Points:
{chr(10).join(f"- {elem}" for elem in expected)}

Candidate Experience Level: {candidate.experience_years} years

Evaluate the response on these dimensions (0-5 scale):
1. **Technical Accuracy**: Correctness of information and concepts
2. **Depth of Understanding**: How deeply the candidate understands the topic
3. **Communication Clarity**: How clearly the candidate explains their thoughts
4. **Relevance**: How well the response addresses the question

Provide:
- Scores for each dimension (0.0 to 5.0)
- 2-3 specific strengths in the response
- 1-2 gaps or areas that could be improved
- Constructive feedback (2-3 sentences)

Return as JSON with fields: technical_accuracy, depth, clarity, relevance, strengths (array), gaps (array), feedback (string)
"""

        return prompt

    def _fallback_evaluation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return fallback evaluation if LLM fails."""
        evaluation = ResponseEvaluation(
            question=context.get("question", ""),
            response=context.get("response", ""),
            topic=context.get("topic", ""),
            timestamp=datetime.now(),
            technical_accuracy=3.0,
            depth=3.0,
            clarity=3.0,
            relevance=3.0,
            overall_score=3.0,
            strengths=["Response provided"],
            gaps=["Unable to evaluate due to technical error"],
            feedback="Thank you for your response. Due to a technical issue, we'll continue with the next question."
        )
        return {"evaluation": evaluation}
