"""Topic manager agent for controlling interview flow."""
import json
from typing import Dict, Any, Optional, List
from .base import BaseAgent
from ..models.candidate import Topic


class TopicManagerAgent(BaseAgent):
    """Agent responsible for managing topic transitions and depth."""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine if topic should transition and suggest next topic.

        Context should include:
            - current_topic: Topic object
            - all_topics: List[Topic]
            - recent_scores: List[float]
            - questions_in_topic: int
            - total_questions: int
            - min_questions_per_topic: int
            - max_questions_per_topic: int

        Returns:
            {
                "should_transition": bool,
                "next_topic": Optional[str],
                "next_depth": Optional[str],
                "reasoning": str
            }
        """
        current_topic = context.get("current_topic")
        questions_count = context.get("questions_in_topic", 0)
        recent_scores = context.get("recent_scores", [])
        min_questions = context.get("min_questions_per_topic", 2)
        max_questions = context.get("max_questions_per_topic", 4)

        self.logger.info(
            f"🔄 TopicManagerAgent: Evaluating topic transition: {current_topic.name}, "
            f"questions={questions_count}, avg_score={sum(recent_scores)/len(recent_scores) if recent_scores else 0}"
        )

        try:
            # Rule-based decision first
            self.logger.info(f"🔄 TopicManagerAgent: Applying rule-based decision logic...")
            rule_decision = self._rule_based_decision(
                questions_count, recent_scores, min_questions, max_questions
            )

            if rule_decision["should_transition"]:
                # Use LLM to select next topic
                self.logger.info(f"🔄 TopicManagerAgent: Transition approved, selecting next topic...")
                next_topic_decision = await self._select_next_topic(context)
                self.logger.info(f"🔄 TopicManagerAgent: Next topic selected: {next_topic_decision['topic']}")
                return {
                    "should_transition": True,
                    "next_topic": next_topic_decision["topic"],
                    "next_depth": next_topic_decision["depth"],
                    "reasoning": next_topic_decision["reasoning"]
                }
            else:
                # Determine if we should go deeper in current topic
                should_deepen = questions_count >= 2 and recent_scores and sum(recent_scores) / len(recent_scores) >= 3.5
                new_depth = "deep" if should_deepen and current_topic.depth == "surface" else current_topic.depth

                return {
                    "should_transition": False,
                    "next_topic": None,
                    "next_depth": new_depth,
                    "reasoning": rule_decision["reasoning"]
                }

        except Exception as e:
            self.logger.error(f"Error in topic management: {str(e)}")
            return {
                "should_transition": False,
                "next_topic": None,
                "next_depth": current_topic.depth,
                "reasoning": "Continuing current topic due to error"
            }

    def _rule_based_decision(
        self,
        questions_count: int,
        recent_scores: List[float],
        min_questions: int,
        max_questions: int
    ) -> Dict[str, Any]:
        """Apply rule-based logic for topic transition."""

        # Rule 1: Must ask minimum questions
        if questions_count < min_questions:
            return {
                "should_transition": False,
                "reasoning": f"Need at least {min_questions} questions per topic"
            }

        # Rule 2: Force transition if max questions reached
        if questions_count >= max_questions:
            return {
                "should_transition": True,
                "reasoning": f"Maximum {max_questions} questions per topic reached"
            }

        # Rule 3: Transition if performing well (avg score > 3.5) and min questions met
        if recent_scores and questions_count >= min_questions:
            avg_score = sum(recent_scores) / len(recent_scores)
            if avg_score >= 3.5:
                return {
                    "should_transition": True,
                    "reasoning": f"Strong performance (avg {avg_score:.1f}/5.0), moving to next topic"
                }

        # Rule 4: Continue current topic
        return {
            "should_transition": False,
            "reasoning": "Continuing current topic for deeper exploration"
        }

    async def _select_next_topic(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to intelligently select next topic."""
        all_topics = context.get("all_topics", [])
        current_topic = context.get("current_topic")
        candidate = context.get("candidate_profile")
        job = context.get("job_requirements")

        # Filter uncovered topics
        uncovered = [t for t in all_topics if not t.covered and t.name != current_topic.name]

        if not uncovered:
            return {
                "topic": None,
                "depth": "surface",
                "reasoning": "All topics covered"
            }

        # If only one topic left, return it
        if len(uncovered) == 1:
            return {
                "topic": uncovered[0].name,
                "depth": "surface",
                "reasoning": "Last remaining topic"
            }

        # Use LLM for intelligent selection
        try:
            prompt = self._build_selection_prompt(current_topic, uncovered, candidate, job)

            response = await self.llm.generate_structured(
                prompt=prompt,
                system_message="You are an expert interviewer managing interview flow.",
                response_format={
                    "next_topic": "string",
                    "depth": "string (surface or deep)",
                    "reasoning": "string"
                }
            )

            return {
                "topic": response["next_topic"],
                "depth": response.get("depth", "surface"),
                "reasoning": response["reasoning"]
            }

        except Exception as e:
            self.logger.error(f"Error selecting next topic: {str(e)}")
            # Fallback: select highest priority uncovered topic
            next_topic = max(uncovered, key=lambda t: t.priority)
            return {
                "topic": next_topic.name,
                "depth": "surface",
                "reasoning": "Selected highest priority remaining topic"
            }

    def _build_selection_prompt(
        self,
        current_topic: Topic,
        uncovered_topics: List[Topic],
        candidate: Any,
        job: Any
    ) -> str:
        """Build prompt for topic selection."""
        topics_list = "\n".join([f"- {t.name} (priority: {t.priority})" for t in uncovered_topics])

        prompt = f"""You are managing the flow of a technical interview.

Current Topic: {current_topic.name} (now completed)
Candidate Experience: {candidate.experience_years} years
Target Role: {job.title}

Remaining Topics:
{topics_list}

Select the best next topic to explore that:
1. Flows naturally from {current_topic.name}
2. Is critical for the {job.title} role
3. Aligns with the candidate's background
4. Maintains interview engagement

Return JSON with:
- "next_topic": The name of the next topic (must match one from the list)
- "depth": "surface" (for introduction) or "deep" (for detailed exploration)
- "reasoning": Brief explanation (1 sentence)
"""

        return prompt
