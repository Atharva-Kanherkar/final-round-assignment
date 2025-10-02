"""Parsers for resume and job description files."""
import re
from typing import List, Dict, Any
import logging

from ..models.candidate import CandidateProfile, JobRequirements, Topic
from ..utils.validators import InputValidator
from ..utils.exceptions import InvalidResumeError, InvalidJobDescriptionError, NoTopicsError


class ResumeParser:
    """Parse resume text to extract candidate information."""

    def __init__(self, logger: logging.Logger):
        """Initialize parser with logger."""
        self.logger = logger

    def parse(self, resume_text: str) -> CandidateProfile:
        """
        Parse resume text into CandidateProfile.

        Args:
            resume_text: Raw resume text

        Returns:
            CandidateProfile object

        Raises:
            InvalidResumeError: If resume is invalid
        """
        self.logger.info("Parsing resume")

        # Validate and sanitize input
        try:
            resume_text = InputValidator.validate_resume(resume_text)
        except InvalidResumeError as e:
            self.logger.error(f"Resume validation failed: {str(e)}")
            raise

        # Extract name (usually first line)
        lines = [line.strip() for line in resume_text.split('\n') if line.strip()]
        name = lines[0] if lines else "Unknown Candidate"

        # Extract skills
        skills = self._extract_skills(resume_text)

        # Edge case: No skills found
        if not skills or len(skills) == 0:
            self.logger.warning("No skills extracted from resume, using generic skills")
            skills = ["Problem Solving", "Communication", "Teamwork"]

        # Extract experience years
        experience_years = self._extract_experience_years(resume_text)

        # Extract education
        education = self._extract_education(resume_text)

        # Extract past roles
        past_roles = self._extract_roles(resume_text)

        # Generate summary
        summary = f"{name} - {experience_years} years experience in {', '.join(skills[:3])}"

        profile = CandidateProfile(
            name=name,
            skills=skills,
            experience_years=experience_years,
            education=education,
            past_roles=past_roles,
            summary=summary,
            raw_resume=resume_text
        )

        self.logger.info(f"Parsed profile for {name} with {len(skills)} skills")
        return profile

    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text."""
        skills = []

        # Look for skills section
        skills_match = re.search(r'Skills?:(.*?)(?=\n[A-Z]|\n\n|Experience:|Education:|$)', text, re.IGNORECASE | re.DOTALL)
        if skills_match:
            skills_text = skills_match.group(1)
            # Split by common delimiters
            raw_skills = re.split(r'[,;\n•\-]', skills_text)
            skills = [s.strip() for s in raw_skills if s.strip() and len(s.strip()) > 2]

        # If no skills section, look for common tech keywords
        if not skills:
            tech_keywords = [
                'Python', 'JavaScript', 'Java', 'C++', 'React', 'Node.js', 'AWS', 'Docker',
                'Kubernetes', 'SQL', 'MongoDB', 'Git', 'Linux', 'TypeScript', 'Go', 'Ruby',
                'Django', 'Flask', 'Vue', 'Angular', 'PostgreSQL', 'Redis', 'Jenkins'
            ]
            for keyword in tech_keywords:
                if re.search(rf'\b{keyword}\b', text, re.IGNORECASE):
                    skills.append(keyword)

        return skills[:15]  # Limit to top 15 skills

    def _extract_experience_years(self, text: str) -> int:
        """Extract years of experience from resume."""
        # Look for patterns like "5 years experience", "5+ years", etc.
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'experience[:\s]+(\d+)\+?\s*years?',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))

        # Try to infer from employment dates
        year_matches = re.findall(r'\b(19|20)\d{2}\b', text)
        if len(year_matches) >= 2:
            years = [int(y) for y in year_matches]
            earliest = min(years)
            latest = max(years)
            return latest - earliest

        return 3  # Default to 3 years if can't determine

    def _extract_education(self, text: str) -> str:
        """Extract education information."""
        education_match = re.search(r'Education:(.*?)(?=\n[A-Z]|\n\n|$)', text, re.IGNORECASE | re.DOTALL)
        if education_match:
            edu_text = education_match.group(1).strip()
            # Get first line
            first_line = edu_text.split('\n')[0].strip()
            return first_line if first_line else "Not specified"

        # Look for degree keywords
        degree_patterns = [
            r'(Bachelor|Master|PhD|B\.S\.|M\.S\.|B\.A\.|M\.A\.).*?(?=\n|$)',
            r'(BS|MS|BA|MA)\s+(?:in\s+)?[\w\s]+(?:,|\n|$)'
        ]

        for pattern in degree_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return "Not specified"

    def _extract_roles(self, text: str) -> List[Dict[str, str]]:
        """Extract past roles/employment history."""
        roles = []

        # Look for experience section
        exp_match = re.search(r'Experience:(.*?)(?=\nEducation:|\n[A-Z][a-z]+:|$)', text, re.IGNORECASE | re.DOTALL)
        if exp_match:
            exp_text = exp_match.group(1)

            # Look for company-role patterns
            role_patterns = [
                r'[-•]\s*([^()\n]+?)\s*\((\d{4}[-–]\d{4}|\d{4}[-–]Present)\)',
                r'([A-Z][^(\n]{10,50}?)\s*\((\d{4}[-–]\d{4}|\d{4}[-–]Present)\)',
            ]

            for pattern in role_patterns:
                matches = re.finditer(pattern, exp_text)
                for match in matches:
                    company_role = match.group(1).strip()
                    duration = match.group(2)

                    # Try to split company and role
                    if ',' in company_role:
                        parts = company_role.split(',')
                        role = parts[0].strip()
                        company = parts[1].strip() if len(parts) > 1 else "Unknown"
                    else:
                        role = company_role
                        company = "Unknown"

                    roles.append({
                        "company": company,
                        "role": role,
                        "duration": duration
                    })

        return roles[:5]  # Limit to 5 most recent


class JobDescriptionParser:
    """Parse job description to extract requirements."""

    def __init__(self, logger: logging.Logger):
        """Initialize parser with logger."""
        self.logger = logger

    def parse(self, jd_text: str) -> JobRequirements:
        """
        Parse job description into JobRequirements.

        Args:
            jd_text: Raw job description text

        Returns:
            JobRequirements object

        Raises:
            InvalidJobDescriptionError: If JD is invalid
        """
        self.logger.info("Parsing job description")

        # Validate and sanitize input
        try:
            jd_text = InputValidator.validate_job_description(jd_text)
        except InvalidJobDescriptionError as e:
            self.logger.error(f"Job description validation failed: {str(e)}")
            raise

        lines = [line.strip() for line in jd_text.split('\n') if line.strip()]

        # Extract title (usually first line, truncate to 250 chars to fit DB)
        title = lines[0] if lines else "Unknown Position"
        if len(title) > 250:
            title = title[:250].rsplit(' ', 1)[0] + "..."  # Truncate at word boundary

        # Extract company
        company = self._extract_company(jd_text)

        # Extract required skills
        required_skills = self._extract_required_skills(jd_text)

        # Extract preferred skills
        preferred_skills = self._extract_preferred_skills(jd_text)

        # Extract responsibilities
        responsibilities = self._extract_responsibilities(jd_text)

        # Extract experience requirement
        experience_required = self._extract_experience_requirement(jd_text)

        job_req = JobRequirements(
            title=title,
            company=company,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            responsibilities=responsibilities,
            experience_required=experience_required,
            raw_description=jd_text
        )

        self.logger.info(f"Parsed job: {title} at {company}")
        return job_req

    def _extract_company(self, text: str) -> str:
        """Extract company name."""
        company_match = re.search(r'Company:\s*(.+)', text, re.IGNORECASE)
        if company_match:
            return company_match.group(1).strip()
        return "Unknown Company"

    def _extract_required_skills(self, text: str) -> List[str]:
        """Extract required skills."""
        skills = []

        # Look for requirements section
        req_match = re.search(r'Requirements?:(.*?)(?=\n[A-Z][a-z]+:|Responsibilities:|$)', text, re.IGNORECASE | re.DOTALL)
        if req_match:
            req_text = req_match.group(1)
            # Extract bullet points or lines
            lines = [line.strip('- •\t') for line in req_text.split('\n') if line.strip()]
            skills = [line for line in lines if line and len(line) > 5]

        return skills[:10]  # Top 10 requirements

    def _extract_preferred_skills(self, text: str) -> List[str]:
        """Extract preferred/nice-to-have skills."""
        skills = []

        patterns = [
            r'Preferred:(.*?)(?=\n[A-Z][a-z]+:|$)',
            r'Nice to have:(.*?)(?=\n[A-Z][a-z]+:|$)',
            r'Bonus:(.*?)(?=\n[A-Z][a-z]+:|$)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                pref_text = match.group(1)
                lines = [line.strip('- •\t') for line in pref_text.split('\n') if line.strip()]
                skills.extend([line for line in lines if line and len(line) > 5])

        return skills[:5]

    def _extract_responsibilities(self, text: str) -> List[str]:
        """Extract job responsibilities."""
        responsibilities = []

        resp_match = re.search(r'Responsibilities?:(.*?)(?=\n[A-Z][a-z]+:|Requirements?:|$)', text, re.IGNORECASE | re.DOTALL)
        if resp_match:
            resp_text = resp_match.group(1)
            lines = [line.strip('- •\t') for line in resp_text.split('\n') if line.strip()]
            responsibilities = [line for line in lines if line and len(line) > 10]

        return responsibilities[:8]

    def _extract_experience_requirement(self, text: str) -> int:
        """Extract required years of experience."""
        pattern = r'(\d+)\+?\s*years?\s*(?:of\s*)?experience'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 0


class TopicGenerator:
    """Generate interview topics from candidate profile and job requirements."""

    def __init__(self, logger: logging.Logger):
        """Initialize generator with logger."""
        self.logger = logger

    def generate_topics(
        self,
        candidate_profile: CandidateProfile,
        job_requirements: JobRequirements,
        max_topics: int = 5
    ) -> List[Topic]:
        """
        Generate prioritized interview topics.

        Args:
            candidate_profile: Candidate's profile
            job_requirements: Job requirements
            max_topics: Maximum number of topics to generate

        Returns:
            List of Topic objects
        """
        self.logger.info("Generating interview topics")

        topics_dict = {}

        # Add topics from candidate skills that match job requirements
        for skill in candidate_profile.skills:
            for req_skill in job_requirements.required_skills:
                if skill.lower() in req_skill.lower() or req_skill.lower() in skill.lower():
                    topics_dict[skill] = 5  # High priority - matches requirements

        # Add topics from candidate skills not in requirements (lower priority)
        for skill in candidate_profile.skills[:5]:  # Top 5 skills
            if skill not in topics_dict:
                topics_dict[skill] = 3  # Medium priority

        # Add general topics relevant to the role
        if "backend" in job_requirements.title.lower() or "senior" in job_requirements.title.lower():
            if "System Design" not in topics_dict:
                topics_dict["System Design"] = 5

        # Convert to Topic objects
        topics = []
        for topic_name, priority in sorted(topics_dict.items(), key=lambda x: x[1], reverse=True)[:max_topics]:
            topics.append(Topic(
                name=topic_name,
                priority=priority,
                depth="surface",
                questions_asked=0,
                covered=False
            ))

        self.logger.info(f"Generated {len(topics)} topics: {[t.name for t in topics]}")
        return topics
