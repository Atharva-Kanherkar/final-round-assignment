#!/usr/bin/env python3
"""Main entry point for AI Mock Interview System."""
import asyncio
import sys
import os
from pathlib import Path

from src.utils.config import load_config
from src.utils.logger import setup_logger, InterviewLogger
from src.services.llm_client import LLMClient
from src.services.parser import ResumeParser, JobDescriptionParser, TopicGenerator
from src.services.metrics import MetricsCollector
from src.agents.orchestrator import OrchestratorAgent
from src.cli.interface import InterviewCLI


async def main():
    """Main function to run the interview system."""
    print("🚀 Starting AI Mock Interview System...\n")

    try:
        # Load configuration
        config = load_config()
        print(f"✓ Configuration loaded (Model: {config.model_name})")

        # Setup logging
        log_file = f"logs/interview_{config.data_dir.replace('/', '_')}.log"
        os.makedirs("logs", exist_ok=True)

        logger = setup_logger(
            name="mock_interview",
            level=config.log_level,
            log_file=log_file
        )
        interview_logger = InterviewLogger(logger)
        print(f"✓ Logging configured (Level: {config.log_level})")

        # Initialize services
        llm_client = LLMClient(
            api_key=config.openai_api_key,
            model_name=config.model_name,
            timeout=config.timeout_seconds,
            max_retries=config.max_retries,
            logger=logger
        )
        print(f"✓ LLM client initialized")

        metrics_collector = MetricsCollector(logger)
        print(f"✓ Metrics collector ready")

        # Initialize parsers
        resume_parser = ResumeParser(logger)
        jd_parser = JobDescriptionParser(logger)
        topic_generator = TopicGenerator(logger)
        print(f"✓ Parsers initialized")

        # Load input files
        data_dir = Path(config.data_dir)

        resume_file = data_dir / "sample_resume.txt"
        jd_file = data_dir / "sample_job_description.txt"

        if not resume_file.exists():
            print(f"\n❌ Error: Resume file not found at {resume_file}")
            print("Please create data/sample_resume.txt with candidate information.")
            return

        if not jd_file.exists():
            print(f"\n❌ Error: Job description file not found at {jd_file}")
            print("Please create data/sample_job_description.txt with job details.")
            return

        print("\n📄 Loading input files...")
        with open(resume_file, 'r') as f:
            resume_text = f.read()

        with open(jd_file, 'r') as f:
            jd_text = f.read()

        print(f"✓ Loaded resume ({len(resume_text)} characters)")
        print(f"✓ Loaded job description ({len(jd_text)} characters)")

        # Parse inputs
        print("\n🔍 Parsing inputs...")
        metrics_collector.start_timer("parse_inputs")

        candidate_profile = resume_parser.parse(resume_text)
        job_requirements = jd_parser.parse(jd_text)
        topics = topic_generator.generate_topics(
            candidate_profile,
            job_requirements,
            max_topics=config.total_topics_target
        )

        metrics_collector.stop_timer("parse_inputs")

        print(f"✓ Candidate: {candidate_profile.name}")
        print(f"✓ Position: {job_requirements.title} at {job_requirements.company}")
        print(f"✓ Topics generated: {', '.join([t.name for t in topics])}")

        # Initialize orchestrator
        orchestrator = OrchestratorAgent(llm_client, logger)
        print(f"✓ Orchestrator initialized with 4 agents")

        # Create interview session
        print("\n🎬 Creating interview session...")
        session = orchestrator.create_session(
            candidate_profile=candidate_profile,
            job_requirements=job_requirements,
            topics=topics
        )

        interview_logger.session_start(
            session_id=session.session_id,
            candidate_name=candidate_profile.name,
            job_title=job_requirements.title
        )

        print(f"✓ Session created: {session.session_id}")

        # Initialize CLI and run interview
        cli_config = {
            "min_questions_per_topic": config.questions_per_topic_min,
            "max_questions_per_topic": config.questions_per_topic_max
        }

        cli = InterviewCLI(orchestrator, cli_config)

        print("\n" + "=" * 80)
        print("\n")

        # Start metrics timer
        metrics_collector.start_timer("total_interview")

        # Run the interview
        await cli.run_interview(session)

        # Stop metrics timer
        duration = metrics_collector.stop_timer("total_interview")

        # Log session end
        interview_logger.session_end(
            session_id=session.session_id,
            duration_minutes=duration / 60.0,
            questions_asked=session.questions_asked
        )

        # Log metrics summary
        metrics_collector.log_summary()

        print("\n✅ Interview system completed successfully!")

    except ValueError as e:
        print(f"\n❌ Configuration error: {str(e)}")
        print("Please check your .env file and ensure OPENAI_API_KEY is set.")
        sys.exit(1)

    except FileNotFoundError as e:
        print(f"\n❌ File not found: {str(e)}")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interview interrupted by user.")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
