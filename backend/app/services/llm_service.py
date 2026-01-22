"""LLM service for Deepseek API integration."""
import json
import logging
from typing import Dict, List, Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import tiktoken
from openai import AsyncOpenAI, OpenAIError

from app.config.llm_config import llm_config

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with Deepseek LLM API."""
    
    def __init__(self):
        """Initialize LLM client with configuration."""
        # Check if API key is available
        if not llm_config.api_key:
            logger.warning("LLM API key not configured. LLM features will be disabled.")
            self.client = None
            self.model = None
            self.max_tokens = 0
            self.temperature = 0.0
            self.tokenizer = None
            return
        
        # Ensure model is not None
        model = llm_config.model or "deepseek-chat"
        
        self.client = AsyncOpenAI(
            api_key=llm_config.api_key,
            base_url=llm_config.base_url,
            timeout=llm_config.timeout
        )
        self.model = model
        self.max_tokens = llm_config.max_tokens
        self.temperature = llm_config.temperature
        
        # Initialize tokenizer for cost estimation
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-4")  # Use GPT-4 as approximation
        except:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text for cost estimation."""
        if not self.tokenizer:
            return 0
        return len(self.tokenizer.encode(text))
    
    @retry(
        stop=stop_after_attempt(llm_config.max_retries),
        wait=wait_exponential(multiplier=llm_config.retry_delay),
        reraise=True
    )
    async def _call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> tuple[str, dict]:
        """Call LLM API with retry logic."""
        if not self.client or not self.model:
            raise RuntimeError("LLM client not initialized. API key may be missing.")
        
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}  # Request JSON response
            )
            
            content = response.choices[0].message.content or ""
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            logger.info(f"LLM call completed. Tokens used: {tokens_used}")
            
            # Store metadata if tracking enabled
            metadata = {}
            if llm_config.enable_token_tracking:
                metadata = {
                    "tokens_used": tokens_used,
                    "model": self.model,
                    "has_response": bool(content)
                }
            
            return content, metadata
            
        except OpenAIError as e:
            logger.error(f"LLM API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in LLM call: {e}")
            raise
    
    async def analyze_vulnerability(self, code: str, context: str = "") -> Dict[str, Any]:
        """
        Analyze Rust code for vulnerabilities using LLM.
        
        Returns structured analysis including:
        - vulnerability_type
        - cwe_id
        - owasp_category
        - risk_level
        - confidence_score
        - vulnerability_description
        - exploitation_scenario
        - line_numbers
        """
        # Check if LLM client is available
        if not self.client:
            logger.warning("LLM client not available. Returning mock analysis.")
            return {
                "vulnerability_type": "None",
                "cwe_id": None,
                "owasp_category": None,
                "risk_level": None,
                "confidence_score": 1.0,
                "vulnerability_description": "LLM analysis disabled (no API key configured)",
                "exploitation_scenario": None,
                "line_numbers": [],
                "llm_metadata": {"disabled": True, "reason": "no_api_key"}
            }
        
        system_prompt = """You are a security expert specializing in Rust code analysis.
        Analyze the provided Rust code for security vulnerabilities.
        Return your analysis in JSON format with the following structure:
        {
            "vulnerability_type": "Description of vulnerability",
            "cwe_id": "CWE-XXX",
            "owasp_category": "A1: Injection",
            "risk_level": "low|medium|high|critical",
            "confidence_score": 0.95,
            "vulnerability_description": "Detailed explanation of the vulnerability",
            "exploitation_scenario": "How attackers could exploit this vulnerability",
            "line_numbers": [start_line, end_line]
        }
        
        If no vulnerability is found, return:
        {
            "vulnerability_type": "None",
            "cwe_id": null,
            "owasp_category": null,
            "risk_level": null,
            "confidence_score": 1.0,
            "vulnerability_description": "No security vulnerabilities detected",
            "exploitation_scenario": null,
            "line_numbers": []
        }
        
        Be specific and technical in your analysis."""
        
        prompt = f"""Analyze this Rust code for security vulnerabilities:
        
        {code}
        
        {f"Additional context: {context}" if context else ""}
        
        Provide your analysis in the specified JSON format."""
        
        metadata = {}  # Initialize metadata
        try:
            response, metadata = await self._call_llm(prompt, system_prompt)
            analysis = json.loads(response)
            
            # Add metadata to analysis
            analysis["llm_metadata"] = metadata
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            # Return fallback analysis
            return {
                "vulnerability_type": "Analysis Error",
                "cwe_id": None,
                "owasp_category": None,
                "risk_level": "medium",
                "confidence_score": 0.0,
                "vulnerability_description": f"Failed to parse LLM analysis: {str(e)}",
                "exploitation_scenario": None,
                "line_numbers": [],
                "llm_metadata": metadata
            }
    
    async def generate_remediation(self, vulnerable_code: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate safe remediation for vulnerable code.
        
        Returns:
        - fixed_code: Safe alternative code
        - explanation: Explanation of changes made
        - compatibility_notes: Any compatibility considerations
        """
        # Check if LLM client is available
        if not self.client:
            logger.warning("LLM client not available. Returning mock remediation.")
            return {
                "fixed_code": vulnerable_code,
                "explanation": "LLM remediation disabled (no API key configured)",
                "compatibility_notes": "Mock remediation - no changes made",
                "llm_metadata": {"disabled": True, "reason": "no_api_key"}
            }
        
        system_prompt = """You are a Rust programming expert specializing in secure code remediation.
        Generate a safe alternative for the vulnerable Rust code.
        Return your response in JSON format:
        {
            "fixed_code": "Safe Rust code here",
            "explanation": "Detailed explanation of security improvements made",
            "compatibility_notes": "Any backward compatibility considerations"
        }
        
        Ensure the fixed code:
        1. Eliminates the security vulnerability
        2. Maintains functionality
        3. Follows Rust best practices
        4. Includes appropriate error handling"""
        
        vulnerability_info = analysis.get("vulnerability_description", "Security vulnerability")
        cwe = analysis.get("cwe_id", "Unknown CWE")
        
        prompt = f"""Generate a safe remediation for this vulnerable Rust code:
        
        Vulnerable Code:
        {vulnerable_code}
        
        Vulnerability: {vulnerability_info}
        CWE: {cwe}
        
        Provide the fixed code and explanation in the specified JSON format."""
        
        metadata = {}  # Initialize metadata
        try:
            response, metadata = await self._call_llm(prompt, system_prompt)
            remediation = json.loads(response)
            
            # Add metadata
            remediation["llm_metadata"] = metadata
            
            return remediation
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse remediation response: {e}")
            return {
                "fixed_code": vulnerable_code,  # Fallback to original
                "explanation": f"Failed to generate remediation: {str(e)}",
                "compatibility_notes": "Remediation generation failed",
                "llm_metadata": metadata
            }
    
    async def verify_remediation(self, original_code: str, fixed_code: str, 
                                analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify that remediation successfully fixes the vulnerability.
        
        Returns:
        - verification_passed: bool
        - verification_explanation: Detailed explanation
        - new_issues: List of any new issues introduced
        """
        # Check if LLM client is available
        if not self.client:
            logger.warning("LLM client not available. Returning mock verification.")
            return {
                "verification_passed": True,
                "verification_explanation": "LLM verification disabled (no API key configured). Assuming remediation is valid.",
                "new_issues": [],
                "llm_metadata": {"disabled": True, "reason": "no_api_key"}
            }
        
        system_prompt = """You are a security verification expert.
        Verify that the fixed code successfully addresses the original vulnerability
        and doesn't introduce new security issues.
        
        Return response in JSON format:
        {
            "verification_passed": true|false,
            "verification_explanation": "Detailed explanation of verification results",
            "new_issues": ["List any new security issues found", "..."]
        }
        
        Be thorough in your analysis."""
        
        vulnerability = analysis.get("vulnerability_description", "Security vulnerability")
        
        prompt = f"""Verify this remediation:
        
        Original Vulnerable Code:
        {original_code}
        
        Fixed Code:
        {fixed_code}
        
        Original Vulnerability: {vulnerability}
        CWE: {analysis.get('cwe_id', 'Unknown')}
        
        Verify that:
        1. The vulnerability is fixed in the fixed code
        2. No new security issues are introduced
        3. The functionality is preserved
        
        Provide verification results in the specified JSON format."""
        
        metadata = {}  # Initialize metadata
        try:
            response, metadata = await self._call_llm(prompt, system_prompt)
            verification = json.loads(response)
            
            # Add metadata
            verification["llm_metadata"] = metadata
            
            return verification
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse verification response: {e}")
            return {
                "verification_passed": False,
                "verification_explanation": f"Verification failed: {str(e)}",
                "new_issues": ["Verification process error"],
                "llm_metadata": metadata
            }
    
    async def complete_analysis_pipeline(self, code: str) -> Dict[str, Any]:
        """
        Complete analysis pipeline: analyze → remediate → verify.
        
        Returns comprehensive analysis results.
        """
        logger.info("Starting LLM analysis pipeline")
        
        # Step 1: Vulnerability analysis
        logger.info("Step 1: Vulnerability analysis")
        vulnerability_analysis = await self.analyze_vulnerability(code)
        
        # If no vulnerability found, return early
        if vulnerability_analysis.get("vulnerability_type") == "None":
            return {
                "vulnerability_analysis": vulnerability_analysis,
                "remediation": None,
                "verification": None,
                "pipeline_complete": True
            }
        
        # Step 2: Generate remediation
        logger.info("Step 2: Generate remediation")
        vulnerable_snippet = code  # In real implementation, extract vulnerable portion
        remediation = await self.generate_remediation(vulnerable_snippet, vulnerability_analysis)
        
        # Step 3: Verify remediation
        logger.info("Step 3: Verify remediation")
        verification = await self.verify_remediation(
            vulnerable_snippet,
            remediation.get("fixed_code", vulnerable_snippet),
            vulnerability_analysis
        )
        
        return {
            "vulnerability_analysis": vulnerability_analysis,
            "remediation": remediation,
            "verification": verification,
            "pipeline_complete": True
        }


# Global LLM service instance
llm_service = LLMService()
