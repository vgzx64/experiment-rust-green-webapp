"""Tests for LLM service - mock-based unit tests."""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock


class TestLLMMocks:
    """Test mocks for LLM service behavior without making real API calls."""
    
    def test_mock_vulnerability_analysis_response(self):
        """Test mock vulnerability analysis response structure."""
        mock_response = {
            "vulnerability_type": "CWE-787: Out-of-bounds Write",
            "cwe_id": "CWE-787",
            "owasp_category": "A1: Injection",
            "risk_level": "critical",
            "confidence_score": 0.95,
            "vulnerability_description": "Buffer overflow vulnerability",
            "exploitation_scenario": "Attacker can overwrite memory",
            "line_numbers": [1, 10]
        }
        
        # Verify response structure
        assert mock_response["vulnerability_type"] == "CWE-787: Out-of-bounds Write"
        assert mock_response["cwe_id"] == "CWE-787"
        assert mock_response["risk_level"] == "critical"
        assert mock_response["confidence_score"] == 0.95
        assert mock_response["line_numbers"] == [1, 10]
    
    def test_mock_remediation_response(self):
        """Test mock remediation response structure."""
        mock_response = {
            "fixed_code": "fn safe_add(a: i32, b: i32) -> i32 { a + b }",
            "explanation": "Use safe arithmetic operations",
            "compatibility_notes": "No breaking changes"
        }
        
        # Verify response structure
        assert "fixed_code" in mock_response
        assert "explanation" in mock_response
        assert "compatibility_notes" in mock_response
    
    def test_mock_json_parsing(self):
        """Test JSON parsing of mock LLM responses."""
        json_string = '{"vulnerability_type": "CWE-123", "cwe_id": "CWE-123"}'
        parsed = json.loads(json_string)
        
        assert parsed["vulnerability_type"] == "CWE-123"
        assert parsed["cwe_id"] == "CWE-123"
    
    def test_mock_difflib_unified_diff(self):
        """Test using difflib for unified diff without LLM."""
        import difflib
        
        original = "line 1\nline 2\nline 3"
        fixed = "line 1\nline 2 modified\nline 3\nline 4"
        
        diff = list(difflib.unified_diff(
            original.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile="original",
            tofile="fixed"
        ))
        
        diff_text = ''.join(diff)
        
        assert "original" in diff_text
        assert "fixed" in diff_text
        assert "+" in diff_text or "-" in diff_text
    
    def test_mock_diff_result_integration(self):
        """Test integrating diff with mock LLM response."""
        import difflib
        
        # Mock LLM response
        mock_original = "fn unsafe() -> i32 { unimplemented!() }"
        mock_fixed = "fn safe() -> Option<i32> { None }"
        
        # Generate diff
        diff = list(difflib.unified_diff(
            mock_original.splitlines(keepends=True),
            mock_fixed.splitlines(keepends=True),
            fromfile="vulnerable_code",
            tofile="remediated_code"
        ))
        
        diff_text = ''.join(diff)
        
        # Verify integration works
        assert "vulnerable_code" in diff_text
        assert "remediated_code" in diff_text
        assert isinstance(diff_text, str)
    
    def test_mock_analysis_pipeline_flow(self):
        """Test mock analysis pipeline flow without API calls."""
        # Step 1: Mock vulnerability detection
        vulnerability_found = True
        mock_analysis = {
            "vulnerability_type": "CWE-252",
            "cwe_id": "CWE-252",
            "risk_level": "high"
        }
        
        # Step 2: Mock remediation (only if vulnerability found)
        if vulnerability_found:
            mock_remediation = {
                "fixed_code": "fn fixed() -> Result<i32, Error> { Ok(42) }",
                "explanation": "Handle errors properly"
            }
        else:
            mock_remediation = None
        
        # Step 3: Generate diff
        import difflib
        diff = list(difflib.unified_diff(
            mock_analysis.get("code", "original").splitlines(keepends=True),
            mock_remediation.get("fixed_code", "fixed").splitlines(keepends=True) if mock_remediation else [],
            fromfile="vulnerable",
            tofile="fixed"
        ))
        
        # Verify flow
        assert vulnerability_found
        assert mock_remediation is not None
        assert "fixed_code" in mock_remediation
    
    def test_mock_no_vulnerability_flow(self):
        """Test mock pipeline when no vulnerability found."""
        mock_analysis = {
            "vulnerability_type": "None",
            "cwe_id": None,
            "risk_level": None
        }
        
        # Should not generate remediation
        remediation = None
        
        if mock_analysis.get("vulnerability_type") == "None":
            diff = ""
        else:
            import difflib
            diff = ''.join(difflib.unified_diff(
                ["code"],
                ["fixed"],
                fromfile="a",
                tofile="b"
            ))
        
        assert remediation is None
        assert diff == ""
    
    def test_mock_error_handling_invalid_json(self):
        """Test mock error handling for invalid JSON."""
        invalid_json = "not valid json"
        
        try:
            parsed = json.loads(invalid_json)
            assert False, "Should have raised JSONDecodeError"
        except json.JSONDecodeError:
            pass  # Expected
    
    def test_mock_error_handling_missing_fields(self):
        """Test mock handling of incomplete LLM responses."""
        # Partial response missing fields
        partial_response = {"vulnerability_type": "Test"}
        
        # Access with defaults
        cwe_id = partial_response.get("cwe_id", "Unknown")
        risk_level = partial_response.get("risk_level", "unknown")
        
        assert cwe_id == "Unknown"
        assert risk_level == "unknown"
    
    def test_mock_confidence_scores(self):
        """Test mock confidence score calculations."""
        # Test various confidence levels
        scores = [0.95, 0.75, 0.50, 0.25]
        
        for score in scores:
            if score >= 0.9:
                level = "high"
            elif score >= 0.7:
                level = "medium"
            else:
                level = "low"
            
            assert isinstance(level, str)
    
    def test_mock_risk_level_mapping(self):
        """Test mock risk level mapping."""
        test_cases = [
            ("critical", "CRITICAL"),
            ("high", "HIGH"),
            ("medium", "MEDIUM"),
            ("low", "LOW"),
        ]
        
        for input_level, expected in test_cases:
            # Mock mapping
            level_map = {
                "critical": "CRITICAL",
                "high": "HIGH", 
                "medium": "MEDIUM",
                "low": "LOW"
            }
            assert level_map[input_level] == expected
    
    def test_mock_line_number_extraction(self):
        """Test mock extraction of line numbers from LLM response."""
        mock_response = {"line_numbers": [5, 15]}
        
        line_start = mock_response["line_numbers"][0]
        line_end = mock_response["line_numbers"][1]
        
        assert line_start == 5
        assert line_end == 15
    
    def test_mock_multiple_vulnerabilities(self):
        """Test mock handling multiple vulnerabilities."""
        mock_vulnerabilities = [
            {"cwe_id": "CWE-787", "risk_level": "critical"},
            {"cwe_id": "CWE-190", "risk_level": "high"},
            {"cwe_id": "CWE-252", "risk_level": "medium"},
        ]
        
        for vuln in mock_vulnerabilities:
            assert "cwe_id" in vuln
            assert "risk_level" in vuln
        
        assert len(mock_vulnerabilities) == 3
    
    def test_mock_retry_logic(self):
        """Test mock retry logic without actual API calls."""
        call_count = 0
        max_retries = 3
        
        def mock_api_call():
            nonlocal call_count
            call_count += 1
            if call_count < max_retries:
                raise Exception("Temporary error")
            return "success"
        
        # Simulate retry
        result = None
        for attempt in range(max_retries):
            try:
                result = mock_api_call()
                break
            except Exception:
                if attempt == max_retries - 1:
                    raise
        
        assert result == "success"
        assert call_count == 3
    
    def test_mock_token_counting(self):
        """Test mock token counting."""
        # Simple word-based token estimation
        text = "fn main() { let x = 42; }"
        estimated_tokens = len(text.split()) * 1.3  # Rough approximation
        
        assert estimated_tokens > 0
        assert isinstance(estimated_tokens, float)
    
    def test_mock_system_prompt_structure(self):
        """Test mock system prompt structure."""
        system_prompt = """You are a security expert specializing in Rust code analysis.
Analyze the provided Rust code for security vulnerabilities.
Return your analysis in JSON format."""
        
        assert "security expert" in system_prompt
        assert "Rust code" in system_prompt
        assert "JSON format" in system_prompt
    
    def test_mock_user_prompt_structure(self):
        """Test mock user prompt structure."""
        code = "fn test() {}"
        vulnerability_info = "CWE-787"
        
        prompt = f"""Analyze this Rust code for security vulnerabilities:

{code}

Vulnerability: {vulnerability_info}

Provide concise analysis in the specified JSON format."""
        
        assert code in prompt
        assert vulnerability_info in prompt
    
    def test_mock_remediation_prompt(self):
        """Test mock remediation prompt."""
        vulnerable_code = "unsafe code"
        vulnerability_info = "Buffer overflow"
        cwe = "CWE-787"
        
        prompt = f"""Generate a safe remediation for this vulnerable Rust code:

Vulnerable Code:
{vulnerable_code}

Vulnerability: {vulnerability_info}
CWE: {cwe}

Provide concise remediation in the specified JSON format."""
        
        assert vulnerable_code in prompt
        assert vulnerability_info in prompt
        assert cwe in prompt


class TestDiffGeneratorIntegration:
    """Test integration of diff generator with mock data."""
    
    def test_diff_with_mock_vulnerable_code(self):
        """Test diff with mock vulnerable code."""
        from app.services.diff_generator import DiffGenerator
        
        vulnerable = "fn unsafe_read() { unimplemented!() }"
        fixed = "fn safe_read() -> Result<(), Error> { Ok(()) }"
        
        result = DiffGenerator.generate_diff_result(vulnerable, fixed)
        
        assert result.has_changes is True
        assert result.lines_added > 0
        assert result.lines_removed > 0
    
    def test_diff_with_mock_safe_code(self):
        """Test diff when code is already safe."""
        from app.services.diff_generator import DiffGenerator
        
        safe_code = "fn safe() { println!(\"safe\"); }"
        
        result = DiffGenerator.generate_diff_result(safe_code, safe_code)
        
        assert result.has_changes is False
        assert result.diff_text == ""
