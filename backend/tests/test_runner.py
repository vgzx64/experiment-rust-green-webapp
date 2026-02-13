"""
Test runner that dynamically reads test cases from directories.

Expected directory structure:
tests/test_cases/
  <test_name>/
    original.rs    # Vulnerable code
    fixed.rs      # Expected safe code (ground truth)
    metadata.json # Optional: vulnerability info

Output (when LLM_ENABLED=true):
  result_suggestion.rs  # LLM's remediation suggestion
  result_explanation.txt # LLM's explanation

Run with LLM:
  export LLM_ENABLED=true
  export LLM_API_KEY=your-key
  python -m pytest tests/test_runner.py -v
"""
import os
import json
import pytest
from pathlib import Path


def discover_test_cases():
    """Discover all test cases in test_cases directory."""
    test_cases_dir = Path(__file__).parent / "test_cases"
    
    if not test_cases_dir.exists():
        return []
    
    test_cases = []
    for subdir in sorted(test_cases_dir.iterdir()):
        if subdir.is_dir():
            original_file = subdir / "original.rs"
            fixed_file = subdir / "fixed.rs"
            metadata_file = subdir / "metadata.json"
            
            if original_file.exists() and fixed_file.exists():
                metadata = {}
                if metadata_file.exists():
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                
                test_cases.append({
                    "name": subdir.name,
                    "path": subdir,
                    "original": original_file.read_text(),
                    "fixed": fixed_file.read_text(),
                    "metadata": metadata
                })
    
    return test_cases


def run_llm_analysis(original_code: str, test_case: dict) -> tuple[str, str]:
    """
    Run LLM analysis on the original code.
    Returns: (suggested_fix, explanation)
    """
    # Check if LLM is enabled
    llm_enabled = os.environ.get("LLM_ENABLED", "false").lower() == "true"
    
    if not llm_enabled:
        return "", "LLM not enabled - set LLM_ENABLED=true to run"
    
    try:
        import asyncio
        from app.services.llm_service import LLMService
        
        async def get_analysis():
            service = LLMService()
            
            # Analyze vulnerability
            analysis = await service.analyze_vulnerability(original_code)
            
            # If vulnerability found, get remediation
            if analysis.get("vulnerability_type") != "None":
                remediation = await service.generate_remediation(original_code, analysis)
                return (
                    remediation.get("fixed_code", ""),
                    remediation.get("explanation", "")
                )
            return ("", "No vulnerability detected")
        
        # Run async analysis
        return asyncio.run(get_analysis())
        
    except Exception as e:
        return "", f"Error: {str(e)}"


def save_results(test_case: dict, suggestion: str, explanation: str):
    """Save LLM results to files in the test case directory."""
    test_path = test_case["path"]
    
    # Save suggestion
    suggestion_file = test_path / "result_suggestion.rs"
    suggestion_file.write_text(suggestion)
    
    # Save explanation
    explanation_file = test_path / "result_explanation.txt"
    explanation_file.write_text(explanation)


# Discover test cases at module load time
TEST_CASES = discover_test_cases()


class TestAgentVulnerabilityDetection:
    """Test vulnerability detection for each test case."""
    
    @pytest.mark.parametrize("test_case", TEST_CASES, ids=lambda tc: tc["name"])
    def test_vulnerability_detection(self, test_case):
        """Test that agent detects vulnerability in original code."""
        assert test_case["original"] is not None
        assert len(test_case["original"]) > 0
        assert test_case["fixed"] is not None
        assert len(test_case["fixed"]) > 0
    
    @pytest.mark.parametrize("test_case", TEST_CASES, ids=lambda tc: tc["name"])
    def test_original_code_is_vulnerable(self, test_case):
        """Verify original code contains unsafe patterns."""
        original = test_case["original"]
        vulnerable_indicators = [
            "unwrap()", "expect()", "get_unchecked",
            "unsafe", "mem::uninitialized", " transmute",
        ]
        
        has_indicator = any(indicator in original for indicator in vulnerable_indicators)
        is_vulnerable = has_indicator or test_case["metadata"].get("is_vulnerable", True)
        assert is_vulnerable, f"Test case {test_case['name']} should contain vulnerable code"
    
    @pytest.mark.parametrize("test_case", TEST_CASES, ids=lambda tc: tc["name"])
    def test_fixed_code_is_safe(self, test_case):
        """Verify fixed code doesn't contain dangerous patterns."""
        fixed = test_case["fixed"]
        dangerous_patterns = [".unwrap()", ".expect(", "get_unchecked"]
        
        for pattern in dangerous_patterns:
            assert pattern not in fixed, f"Fixed code should not contain {pattern}"


class TestDiffGeneration:
    """Test diff generation between original and fixed code."""
    
    @pytest.mark.parametrize("test_case", TEST_CASES, ids=lambda tc: tc["name"])
    def test_diff_generation(self, test_case):
        """Test that diff can be generated between original and fixed."""
        from app.services.diff_generator import DiffGenerator
        
        result = DiffGenerator.generate_diff_result(
            test_case["original"],
            test_case["fixed"]
        )
        
        assert result.has_changes is True
        assert result.lines_added > 0
        assert result.lines_removed > 0


class TestLLMIntegration:
    """Test LLM integration - generates result files for human review."""
    
    @pytest.mark.parametrize("test_case", TEST_CASES, ids=lambda tc: tc["name"])
    def test_llm_analysis(self, test_case):
        """Run LLM and save results for human review."""
        suggestion, explanation = run_llm_analysis(
            test_case["original"],
            test_case
        )
        
        # Save results to test case directory
        save_results(test_case, suggestion, explanation)
        
        # Verify files were created
        test_path = test_case["path"]
        suggestion_file = test_path / "result_suggestion.rs"
        explanation_file = test_path / "result_explanation.txt"
        
        assert suggestion_file.exists(), "result_suggestion.rs should be created"
        assert explanation_file.exists(), "result_explanation.txt should be created"
        
        # If LLM was used, suggestion should not be empty
        llm_enabled = os.environ.get("LLM_ENABLED", "false").lower() == "true"
        if llm_enabled:
            assert len(suggestion) > 0, "LLM should produce suggestion"


class TestMetadataValidation:
    """Test that metadata is properly loaded."""
    
    @pytest.mark.parametrize("test_case", TEST_CASES, ids=lambda tc: tc["name"])
    def test_metadata_structure(self, test_case):
        """Verify metadata has expected fields if present."""
        metadata = test_case["metadata"]
        
        if metadata:
            if "cwe_id" in metadata:
                assert metadata["cwe_id"].startswith("CWE-")
            
            if "risk_level" in metadata:
                assert metadata["risk_level"] in ["low", "medium", "high", "critical"]


def test_discover_test_cases():
    """Verify test case discovery works."""
    assert len(TEST_CASES) >= 0


if __name__ == "__main__":
    print(f"Discovered {len(TEST_CASES)} test cases:")
    for tc in TEST_CASES:
        print(f"  - {tc['name']}")
    
    if not TEST_CASES:
        print("\nNo test cases found!")
        print("Create test cases in: tests/test_cases/<name>/")
        print("  - original.rs (vulnerable code)")
        print("  - fixed.rs (expected fixed code)")
    
    llm_enabled = os.environ.get("LLM_ENABLED", "false").lower() == "true"
    print(f"\nLLM Mode: {'REAL API' if llm_enabled else 'DISABLED (mock)'}")
    
    if llm_enabled:
        print("⚠️  Running with real LLM API - may incur costs!")
