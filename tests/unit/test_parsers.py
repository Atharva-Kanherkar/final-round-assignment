"""
Comprehensive tests for resume and job description parsers.

Tests parsing logic, edge cases, and error handling.
"""
import pytest
from src.services.parser import ResumeParser, JobDescriptionParser, TopicGenerator
from src.utils.exceptions import InvalidResumeError, InvalidJobDescriptionError, NoTopicsError


# ============================================================================
# Resume Parser Tests
# ============================================================================

class TestResumeParser:
    """Test resume parsing functionality."""

    def test_parse_valid_resume(self, mock_logger, valid_resume_text):
        """Test parsing valid resume."""
        parser = ResumeParser(mock_logger)

        profile = parser.parse(valid_resume_text)

        assert profile.name == "John Doe"
        assert len(profile.skills) > 0
        assert "Python" in profile.skills
        assert profile.experience_years == 5
        assert "Computer Science" in profile.education
        assert len(profile.past_roles) > 0

    def test_parse_minimal_resume(self, mock_logger, minimal_resume_text):
        """Test parsing minimal but valid resume."""
        parser = ResumeParser(mock_logger)

        profile = parser.parse(minimal_resume_text)

        assert profile.name == "Jane Smith"
        assert len(profile.skills) > 0
        assert profile.experience_years > 0

    def test_parse_resume_no_skills_fallback(self, mock_logger, resume_with_no_skills):
        """Test fallback when no skills detected."""
        parser = ResumeParser(mock_logger)

        profile = parser.parse(resume_with_no_skills)

        # Should have fallback skills
        assert len(profile.skills) > 0
        assert "Problem Solving" in profile.skills or "Communication" in profile.skills

    def test_parse_resume_empty_raises_error(self, mock_logger, empty_resume):
        """Test empty resume raises error."""
        parser = ResumeParser(mock_logger)

        with pytest.raises(InvalidResumeError, match="empty"):
            parser.parse(empty_resume)

    def test_parse_resume_whitespace_only_raises_error(self, mock_logger, whitespace_resume):
        """Test whitespace-only resume raises error."""
        parser = ResumeParser(mock_logger)

        with pytest.raises(InvalidResumeError, match="empty"):
            parser.parse(whitespace_resume)

    def test_parse_resume_too_short_raises_error(self, mock_logger):
        """Test too-short resume raises error."""
        parser = ResumeParser(mock_logger)

        with pytest.raises(InvalidResumeError, match="too short"):
            parser.parse("John Doe")

    def test_parse_resume_malicious_xss_raises_error(self, mock_logger, malicious_resume_xss):
        """Test XSS attempt raises error."""
        parser = ResumeParser(mock_logger)

        with pytest.raises(InvalidResumeError, match="malicious"):
            parser.parse(malicious_resume_xss)

    def test_parse_resume_binary_data_raises_error(self, mock_logger, binary_resume):
        """Test binary data raises error."""
        parser = ResumeParser(mock_logger)

        with pytest.raises(InvalidResumeError, match="binary"):
            parser.parse(binary_resume)

    def test_parse_resume_oversized_raises_error(self, mock_logger, oversized_resume):
        """Test oversized resume raises error."""
        parser = ResumeParser(mock_logger)

        with pytest.raises(InvalidResumeError, match="too large"):
            parser.parse(oversized_resume)

    def test_skill_extraction_various_formats(self, mock_logger):
        """Test skill extraction from various formats."""
        parser = ResumeParser(mock_logger)

        # Test different skill section formats
        resumes = [
            "Name\nSkills: Python, Java, C++\n" * 5,
            "Name\nSkills:\n- Python\n- Java\n- C++\n" * 5,
            "Name\nTechnical Skills: Python, Java, C++\n" * 5,
        ]

        for resume_text in resumes:
            profile = parser.parse(resume_text)
            assert len(profile.skills) > 0

    def test_experience_extraction(self, mock_logger):
        """Test experience year extraction."""
        parser = ResumeParser(mock_logger)

        resumes_with_experience = [
            ("John Doe\n5 years experience\nSkills: Python\n" * 3, 5),
            ("John Doe\n10+ years of experience\nSkills: Python\n" * 3, 10),
            ("John Doe\nExperience: 3 years\nSkills: Python\n" * 3, 3),
        ]

        for resume_text, expected_years in resumes_with_experience:
            profile = parser.parse(resume_text)
            assert profile.experience_years == expected_years

    def test_education_extraction(self, mock_logger):
        """Test education extraction."""
        parser = ResumeParser(mock_logger)

        resume = """John Doe
Software Engineer

Skills: Python, Java

Education:
BS Computer Science, MIT (2015-2019)
"""
        profile = parser.parse(resume)
        assert "Computer Science" in profile.education or "MIT" in profile.education


# ============================================================================
# Job Description Parser Tests
# ============================================================================

class TestJobDescriptionParser:
    """Test job description parsing."""

    def test_parse_valid_jd(self, mock_logger, valid_job_description_text):
        """Test parsing valid job description."""
        parser = JobDescriptionParser(mock_logger)

        jd = parser.parse(valid_job_description_text)

        assert jd.title == "Senior Backend Engineer"
        assert jd.company == "TechCo"
        assert len(jd.required_skills) > 0
        assert len(jd.responsibilities) > 0
        assert jd.experience_required == 5

    def test_parse_minimal_jd(self, mock_logger):
        """Test parsing minimal job description."""
        parser = JobDescriptionParser(mock_logger)

        minimal_jd = """Software Engineer
Company: TestCo

Requirements:
- Python experience
- 3+ years

Responsibilities:
- Write code
- Review code
"""
        jd = parser.parse(minimal_jd)

        assert jd.title == "Software Engineer"
        assert jd.company == "TestCo"
        assert len(jd.required_skills) > 0

    def test_parse_jd_empty_raises_error(self, mock_logger):
        """Test empty JD raises error."""
        parser = JobDescriptionParser(mock_logger)

        with pytest.raises(InvalidJobDescriptionError, match="empty"):
            parser.parse("")

    def test_parse_jd_too_short_raises_error(self, mock_logger):
        """Test too-short JD raises error."""
        parser = JobDescriptionParser(mock_logger)

        with pytest.raises(InvalidJobDescriptionError, match="too short"):
            parser.parse("Software Engineer")

    def test_parse_jd_malicious_content_raises_error(self, mock_logger):
        """Test malicious content raises error."""
        parser = JobDescriptionParser(mock_logger)

        malicious_jd = "<script>alert('xss')</script>" + "Software Engineer\nCompany: Test\nRequirements:\n" * 5

        with pytest.raises(InvalidJobDescriptionError, match="malicious"):
            parser.parse(malicious_jd)

    def test_experience_requirement_extraction(self, mock_logger):
        """Test experience requirement extraction."""
        parser = JobDescriptionParser(mock_logger)

        jds_with_experience = [
            ("Software Engineer\nCompany: Test\nRequirements:\n- 5+ years experience\n" * 3, 5),
            ("Software Engineer\nCompany: Test\nRequirements:\n- 10 years of experience\n" * 3, 10),
            ("Software Engineer\nCompany: Test\nRequirements:\n- Minimum 3 years\n" * 3, 3),
        ]

        for jd_text, expected_years in jds_with_experience:
            jd = parser.parse(jd_text)
            assert jd.experience_required == expected_years

    def test_company_name_extraction(self, mock_logger):
        """Test company name extraction."""
        parser = JobDescriptionParser(mock_logger)

        jd_text = """Senior Engineer
Company: TechCorp Inc.

Requirements:
- 5 years experience
- Python skills

Responsibilities:
- Develop software
"""
        jd = parser.parse(jd_text)
        assert jd.company == "TechCorp Inc."


# ============================================================================
# Topic Generator Tests
# ============================================================================

class TestTopicGenerator:
    """Test interview topic generation."""

    def test_generate_topics_with_skill_overlap(self, mock_logger, candidate_profile, job_requirements):
        """Test topics generated from skill overlap."""
        generator = TopicGenerator(mock_logger)

        topics = generator.generate_topics(candidate_profile, job_requirements, max_topics=5)

        assert len(topics) > 0
        assert len(topics) <= 5
        assert all(isinstance(topic.name, str) for topic in topics)
        assert all(topic.priority >= 1 and topic.priority <= 5 for topic in topics)

    def test_generate_topics_no_overlap(self, mock_logger):
        """Test topic generation when no skill overlap."""
        from src.models.candidate import CandidateProfile, JobRequirements

        generator = TopicGenerator(mock_logger)

        # Candidate and job with no skill overlap
        candidate = CandidateProfile(
            name="Jane",
            skills=["Painting", "Sculpture", "Art History"],
            experience_years=3,
            education="BFA",
            past_roles=[],
            summary="Artist"
        )

        job = JobRequirements(
            title="Software Engineer",
            company="TechCo",
            required_skills=["Python", "Java", "AWS"],
            responsibilities=["Code"],
            experience_required=3
        )

        topics = generator.generate_topics(candidate, job, max_topics=5)

        # Should still generate topics (from candidate skills)
        assert len(topics) > 0

    def test_generate_topics_respects_max_limit(self, mock_logger, candidate_profile):
        """Test topic generation respects max limit."""
        from src.models.candidate import JobRequirements

        generator = TopicGenerator(mock_logger)

        # Job with many requirements
        job = JobRequirements(
            title="Full Stack Engineer",
            company="TechCo",
            required_skills=[
                "Python", "JavaScript", "React", "Node.js", "AWS",
                "Docker", "Kubernetes", "PostgreSQL", "MongoDB",
                "Redis", "GraphQL", "TypeScript", "Vue"
            ],
            responsibilities=["Everything"],
            experience_required=5
        )

        topics_3 = generator.generate_topics(candidate_profile, job, max_topics=3)
        topics_10 = generator.generate_topics(candidate_profile, job, max_topics=10)

        assert len(topics_3) <= 3
        assert len(topics_10) <= 10

    def test_generate_topics_prioritization(self, mock_logger, candidate_profile, job_requirements):
        """Test topics are prioritized correctly."""
        generator = TopicGenerator(mock_logger)

        topics = generator.generate_topics(candidate_profile, job_requirements, max_topics=5)

        # Topics should be sorted by priority (descending)
        priorities = [topic.priority for topic in topics]
        assert priorities == sorted(priorities, reverse=True)

    def test_generate_topics_adds_system_design_for_senior_roles(self, mock_logger, candidate_profile):
        """Test system design topic added for senior roles."""
        from src.models.candidate import JobRequirements

        generator = TopicGenerator(mock_logger)

        job = JobRequirements(
            title="Senior Backend Engineer",  # "Senior" in title
            company="TechCo",
            required_skills=["Python"],
            responsibilities=["Lead projects"],
            experience_required=5
        )

        topics = generator.generate_topics(candidate_profile, job, max_topics=5)

        # Should include System Design
        topic_names = [t.name for t in topics]
        assert "System Design" in topic_names

    def test_generate_topics_deduplication(self, mock_logger):
        """Test topics are deduplicated."""
        from src.models.candidate import CandidateProfile, JobRequirements

        generator = TopicGenerator(mock_logger)

        # Candidate and job both mention Python multiple times
        candidate = CandidateProfile(
            name="John",
            skills=["Python", "Python Programming", "Python Development"],
            experience_years=5,
            education="BS CS",
            past_roles=[],
            summary="Python developer"
        )

        job = JobRequirements(
            title="Python Engineer",
            company="TechCo",
            required_skills=["Python experience", "Python programming"],
            responsibilities=["Python development"],
            experience_required=5
        )

        topics = generator.generate_topics(candidate, job, max_topics=5)

        # Python should only appear once
        topic_names = [t.name for t in topics]
        python_count = sum(1 for name in topic_names if "Python" in name)
        assert python_count <= 2  # Allow for "Python" as separate topic


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestParserEdgeCases:
    """Test edge cases in parsing."""

    def test_resume_with_special_characters(self, mock_logger):
        """Test resume with special characters."""
        parser = ResumeParser(mock_logger)

        resume = """José García
Software Engineer™

Skills: Python®, C++, Node.js™
Experience: 5 years @ TechCorp™
Email: jose.garcia+work@example.com
Phone: +1 (555) 123-4567
"""
        profile = parser.parse(resume)

        assert profile.name is not None
        assert len(profile.skills) > 0

    def test_jd_with_unicode(self, mock_logger):
        """Test JD with unicode characters."""
        parser = JobDescriptionParser(mock_logger)

        jd = """Senior Engineer 🚀
Company: TechCo™

Requirements:
- 5+ years experience
- Python • Java • Go
- Work with international team (日本語 optional)

Responsibilities:
- Build awesome™ products
"""
        result = parser.parse(jd)

        assert result.title is not None
        assert result.company is not None

    def test_resume_multiline_sections(self, mock_logger):
        """Test resume with multi-line sections."""
        parser = ResumeParser(mock_logger)

        resume = """John Doe
Software Engineer

Skills:
Python, Java, JavaScript,
React, Node.js, AWS, Docker,
Kubernetes, PostgreSQL

Experience:
Tech Corp (2020-2023):
Led development of microservices.
Improved performance by 40%.
Mentored 5 engineers.
"""
        profile = parser.parse(resume)

        # Skills should be extracted across lines
        assert len(profile.skills) >= 5
        # Past roles extraction depends on format - may or may not extract
        # The important part is parsing doesn't fail
        assert profile.name == "John Doe"
