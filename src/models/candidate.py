"""Data models for candidate profiles and job requirements."""
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class CandidateProfile:
    """Represents parsed candidate information from resume."""
    name: str
    skills: List[str]
    experience_years: int
    education: str
    past_roles: List[Dict[str, str]]  # [{"company": "...", "role": "...", "duration": "..."}]
    summary: str = ""
    raw_resume: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "skills": self.skills,
            "experience_years": self.experience_years,
            "education": self.education,
            "past_roles": self.past_roles,
            "summary": self.summary
        }


@dataclass
class JobRequirements:
    """Represents parsed job description."""
    title: str
    company: str
    required_skills: List[str]
    preferred_skills: List[str] = field(default_factory=list)
    responsibilities: List[str] = field(default_factory=list)
    experience_required: int = 0
    raw_description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "company": self.company,
            "required_skills": self.required_skills,
            "preferred_skills": self.preferred_skills,
            "responsibilities": self.responsibilities,
            "experience_required": self.experience_required
        }


@dataclass
class Topic:
    """Represents an interview topic."""
    name: str
    priority: int  # 1-5, higher is more important
    depth: str = "surface"  # "surface" | "deep"
    questions_asked: int = 0
    covered: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "priority": self.priority,
            "depth": self.depth,
            "questions_asked": self.questions_asked,
            "covered": self.covered
        }
