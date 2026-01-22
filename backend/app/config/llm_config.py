"""LLM configuration for Deepseek API."""
from pydantic_settings import BaseSettings
from typing import Optional


class LLMConfig(BaseSettings):
    """Configuration for LLM service."""
    
    # Deepseek API configuration
    deepseek_api_key: Optional[str] = None
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: str = "https://api.deepseek.com"
    
    # LLM feature toggle
    use_llm: bool = False
    
    # OpenAI-compatible configuration (for Deepseek)
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    
    # Generation parameters
    max_tokens: int = 4000
    temperature: float = 0.1
    timeout: int = 30  # seconds
    
    # Retry configuration
    max_retries: int = 3
    retry_delay: int = 2  # seconds
    
    # Cost/token tracking
    enable_token_tracking: bool = True
    
    class Config:
        env_file = ".env"
        env_prefix = "DEEPSEEK_"
    
    def __init__(self, **kwargs):
        """Initialize with backward compatibility."""
        super().__init__(**kwargs)
        
        # Set OpenAI-compatible fields from Deepseek fields
        if not self.api_key:
            self.api_key = self.deepseek_api_key
        if not self.model:
            self.model = self.deepseek_model
        if not self.base_url:
            self.base_url = self.deepseek_base_url
        
        # If API key is not set, disable LLM
        if not self.api_key:
            self.use_llm = False


# Global configuration instance
llm_config = LLMConfig()
