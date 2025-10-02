"""Interactive CLI interface for mock interview system."""
import asyncio
import json
import os
from typing import Optional
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.markdown import Markdown

from ..models.session import InterviewSession, SessionStatus
from ..models.evaluation import FinalReport
from ..agents.orchestrator import OrchestratorAgent


class InterviewCLI:
    """Interactive command-line interface for conducting interviews."""

    def __init__(self, orchestrator: OrchestratorAgent, config: dict):
        """
        Initialize CLI interface.

        Args:
            orchestrator: OrchestratorAgent instance
            config: Configuration dictionary
        """
        self.orchestrator = orchestrator
        self.config = config
        self.console = Console()
        self.session: Optional[InterviewSession] = None

    def display_welcome(self) -> None:
        """Display welcome message."""
        welcome_text = """
# 🎯 AI Mock Interview System

Welcome to your personalized technical interview practice session.

This system will conduct a professional technical interview tailored to your
background and the target role. You'll receive real-time feedback on your responses.

**Tips:**
- Take your time to think through your answers
- Be specific and provide examples when possible
- Type 'exit' at any time to end the interview
- Type 'status' to see your current progress
"""
        self.console.print(Panel(Markdown(welcome_text), border_style="blue"))

    def display_interview_context(self, session: InterviewSession) -> None:
        """Display interview context information."""
        context_table = Table(show_header=False, box=None)
        context_table.add_column("Key", style="cyan")
        context_table.add_column("Value", style="white")

        context_table.add_row("Candidate", session.candidate_profile.name)
        context_table.add_row("Position", session.job_requirements.title)
        context_table.add_row("Company", session.job_requirements.company)
        context_table.add_row("Topics", f"{len(session.topics)} topics to cover")
        context_table.add_row("Experience", f"{session.candidate_profile.experience_years} years")

        self.console.print("\n")
        self.console.print(Panel(context_table, title="📋 Interview Context", border_style="green"))
        self.console.print("\n")

    def display_topic_header(self, session: InterviewSession) -> None:
        """Display current topic header."""
        current_topic = session.get_current_topic()
        if not current_topic:
            return

        topic_info = f"""
**Current Topic:** {current_topic.name}
**Depth Level:** {current_topic.depth.upper()}
**Topic Progress:** {session.current_topic_index + 1}/{len(session.topics)}
**Questions in Topic:** {current_topic.questions_asked}
"""

        self.console.print(Panel(
            Markdown(topic_info),
            title=f"📍 Topic {session.current_topic_index + 1}/{len(session.topics)}",
            border_style="yellow"
        ))
        self.console.print("\n")

    def display_question(self, question: str, question_number: int) -> None:
        """Display interview question."""
        self.console.print(f"[bold cyan]Question #{question_number}:[/bold cyan]")
        self.console.print(f"[white]{question}[/white]")
        self.console.print("\n")

    def get_user_response(self) -> str:
        """
        Get multi-line response from user.

        Returns:
            User's response text
        """
        self.console.print("[dim]Your answer (press Enter twice when done, or type 'exit' to quit):[/dim]")

        lines = []
        empty_line_count = 0

        while True:
            try:
                line = input()

                # Check for exit command
                if line.strip().lower() == 'exit':
                    return 'exit'

                # Check for status command
                if line.strip().lower() == 'status':
                    return 'status'

                # Check for empty line
                if not line.strip():
                    empty_line_count += 1
                    if empty_line_count >= 2:
                        break
                    lines.append(line)
                else:
                    empty_line_count = 0
                    lines.append(line)

            except EOFError:
                break
            except KeyboardInterrupt:
                return 'exit'

        response = '\n'.join(lines).strip()
        return response if response else "(No response provided)"

    def display_evaluation(self, evaluation: any) -> None:
        """Display evaluation feedback."""
        # Score display
        score_text = f"**Overall Score:** {'★' * int(evaluation.overall_score)}{'☆' * (5 - int(evaluation.overall_score))} ({evaluation.overall_score:.1f}/5.0)"

        # Detailed scores
        scores_table = Table(show_header=True, box=None, padding=(0, 2))
        scores_table.add_column("Dimension", style="cyan")
        scores_table.add_column("Score", style="yellow", justify="center")

        scores_table.add_row("Technical Accuracy", f"{evaluation.technical_accuracy:.1f}/5.0")
        scores_table.add_row("Depth of Understanding", f"{evaluation.depth:.1f}/5.0")
        scores_table.add_row("Communication Clarity", f"{evaluation.clarity:.1f}/5.0")
        scores_table.add_row("Relevance to Question", f"{evaluation.relevance:.1f}/5.0")

        # Strengths and gaps
        feedback_text = f"\n{score_text}\n\n"

        if evaluation.strengths:
            feedback_text += "**✓ Strengths:**\n"
            for strength in evaluation.strengths:
                feedback_text += f"  • {strength}\n"
            feedback_text += "\n"

        if evaluation.gaps:
            feedback_text += "**⚠ Areas to Improve:**\n"
            for gap in evaluation.gaps:
                feedback_text += f"  • {gap}\n"
            feedback_text += "\n"

        if evaluation.feedback:
            feedback_text += f"**💬 Feedback:**\n{evaluation.feedback}\n"

        self.console.print("\n")
        self.console.print(Panel(
            Markdown(feedback_text),
            title="📊 Response Evaluation",
            border_style="green" if evaluation.overall_score >= 3.5 else "yellow"
        ))
        self.console.print("\n")

    def display_topic_transition(self, from_topic: str, to_topic: str, reasoning: str) -> None:
        """Display topic transition notification."""
        transition_text = f"""
**Transitioning from:** {from_topic}
**Moving to:** {to_topic}

*{reasoning}*
"""

        self.console.print(Panel(
            Markdown(transition_text),
            title="🔄 Topic Transition",
            border_style="blue"
        ))
        self.console.print("\n")

    def display_status(self, session: InterviewSession) -> None:
        """Display current interview status."""
        elapsed = (datetime.now() - session.start_time).total_seconds() / 60.0
        avg_score = session.get_average_score()

        status_table = Table(show_header=False, box=None)
        status_table.add_column("Metric", style="cyan")
        status_table.add_column("Value", style="white")

        status_table.add_row("Session ID", session.session_id[:8])
        status_table.add_row("Current Topic", f"{session.current_topic} ({session.current_topic_index + 1}/{len(session.topics)})")
        status_table.add_row("Questions Asked", str(session.questions_asked))
        status_table.add_row("Elapsed Time", f"{elapsed:.1f} minutes")
        status_table.add_row("Average Score", f"{avg_score:.2f}/5.0" if avg_score > 0 else "N/A")
        status_table.add_row("Topics Covered", str(sum(1 for t in session.topics if t.covered)))

        self.console.print("\n")
        self.console.print(Panel(status_table, title="📈 Interview Status", border_style="cyan"))
        self.console.print("\n")

    def display_final_report(self, report: FinalReport) -> None:
        """Display final interview report."""
        self.console.print("\n")
        self.console.print("=" * 80)
        self.console.print("\n")

        # Header
        header_text = f"""
# 🎓 Final Interview Report

**Candidate:** {report.candidate_name}
**Position:** {report.job_title}
**Date:** {report.interview_date.strftime('%Y-%m-%d %H:%M')}
**Duration:** {report.duration_minutes:.1f} minutes
**Questions Asked:** {report.total_questions}
"""
        self.console.print(Markdown(header_text))

        # Overall score
        stars = '★' * int(report.overall_score) + '☆' * (5 - int(report.overall_score))
        self.console.print(f"\n[bold]Overall Score:[/bold] {stars} [bold yellow]{report.overall_score:.2f}/5.0[/bold yellow]")
        self.console.print(f"[bold]Recommendation:[/bold] [bold {'green' if 'Hire' in report.recommendation else 'yellow'}]{report.recommendation}[/bold {'green' if 'Hire' in report.recommendation else 'yellow'}]\n")

        # Topics covered
        if report.topic_summaries:
            topics_table = Table(title="📚 Topics Covered", show_header=True)
            topics_table.add_column("Topic", style="cyan")
            topics_table.add_column("Questions", justify="center")
            topics_table.add_column("Avg Score", justify="center")

            for summary in report.topic_summaries:
                score_color = "green" if summary.average_score >= 3.5 else "yellow" if summary.average_score >= 3.0 else "red"
                topics_table.add_row(
                    summary.topic,
                    str(summary.questions_count),
                    f"[{score_color}]{summary.average_score:.1f}/5.0[/{score_color}]"
                )

            self.console.print(topics_table)
            self.console.print("\n")

        # Strengths
        if report.overall_strengths:
            self.console.print("[bold green]✓ Key Strengths:[/bold green]")
            for strength in report.overall_strengths:
                self.console.print(f"  • {strength}")
            self.console.print("\n")

        # Areas for improvement
        if report.areas_for_improvement:
            self.console.print("[bold yellow]⚠ Areas for Improvement:[/bold yellow]")
            for area in report.areas_for_improvement:
                self.console.print(f"  • {area}")
            self.console.print("\n")

        # Additional notes
        if report.additional_notes:
            self.console.print(Panel(
                report.additional_notes,
                title="💬 Summary",
                border_style="blue"
            ))

        self.console.print("\n")
        self.console.print("=" * 80)
        self.console.print("\n")
        self.console.print("[bold green]Thank you for completing the interview! Good luck with your job search! 🚀[/bold green]\n")

    async def run_interview(self, session: InterviewSession) -> None:
        """
        Run the complete interview session.

        Args:
            session: InterviewSession object
        """
        self.session = session

        # Display welcome and context
        self.display_welcome()
        self.display_interview_context(session)

        input("\nPress Enter to begin the interview...")

        # Generate first question
        self.console.print("\n[yellow]⏳ Generating first question (calling OpenAI API)...[/yellow]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("🤖 Calling LLM to generate question...", total=None)
            first_question = await self.orchestrator.generate_first_question(session)
            progress.update(task, completed=True)

        self.console.print("[green]✓ Question generated successfully[/green]\n")

        # Main interview loop
        while session.current_topic_index < len(session.topics):
            # Display topic header
            self.display_topic_header(session)

            # Get current question
            last_message = session.conversation_history[-1]
            question = last_message.content

            # Display question
            self.display_question(question, session.questions_asked)

            # Get user response
            response = self.get_user_response()

            # Handle special commands
            if response.lower() == 'exit':
                self.console.print("\n[yellow]Interview terminated by user.[/yellow]\n")
                return

            if response.lower() == 'status':
                self.display_status(session)
                continue

            # Process response
            self.console.print("\n[yellow]⏳ Evaluating your response (calling OpenAI API)...[/yellow]\n")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("🤖 Step 1/3: Calling LLM to evaluate response...", total=None)

                # Show what's happening
                progress.update(task, description="🤖 Step 1/3: Evaluating response...")
                await asyncio.sleep(0.1)

                progress.update(task, description="🤖 Step 2/3: Checking topic transition logic...")
                result = await self.orchestrator.process_response(
                    session=session,
                    candidate_response=response,
                    config=self.config
                )

                progress.update(task, description="🤖 Step 3/3: Generating next question...")
                await asyncio.sleep(0.1)

                progress.update(task, completed=True)

            self.console.print("[green]✓ Processing complete[/green]\n")

            # Display evaluation
            self.display_evaluation(result["evaluation"])

            # Check if interview is complete
            if result["interview_complete"]:
                break

            # Display topic transition if occurred
            if result["transitioned"]:
                current_topic_obj = session.get_current_topic()
                prev_topic = session.topics[session.current_topic_index - 1].name
                self.display_topic_transition(
                    prev_topic,
                    current_topic_obj.name if current_topic_obj else "Unknown",
                    result.get("transition_reasoning", "Moving to next topic")
                )

            # Brief pause before next question
            await asyncio.sleep(1)

        # Generate and display final report
        self.console.print("\n[yellow]⏳ Generating final report (calling OpenAI API)...[/yellow]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("🤖 Analyzing overall performance and generating summary...", total=None)
            final_report = await self.orchestrator.generate_final_report(session)
            progress.update(task, completed=True)

        self.console.print("[green]✓ Final report generated[/green]\n")
        self.display_final_report(final_report)

        # Save session
        self._save_session(session)

    def _save_session(self, session: InterviewSession) -> None:
        """Save session to file."""
        try:
            sessions_dir = "sessions"
            os.makedirs(sessions_dir, exist_ok=True)

            filename = f"{sessions_dir}/session_{session.session_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(filename, 'w') as f:
                json.dump(session.to_dict(), f, indent=2, default=str)

            self.console.print(f"[dim]Session saved to: {filename}[/dim]\n")

        except Exception as e:
            self.console.print(f"[red]Warning: Could not save session: {str(e)}[/red]\n")
