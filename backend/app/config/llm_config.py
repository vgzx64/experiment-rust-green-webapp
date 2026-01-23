import os
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv, find_dotenv


os.chdir("backend")
print(os.getcwd())
if not find_dotenv():
    raise OSError(".env not found")
load_dotenv()


class LLMConfig(BaseSettings):
    """Configuration for LLM service."""
    
    # Core LLM configuration
    api_key: Optional[str] = os.environ['LLM_API_KEY'] or None
    model: str = "deepseek-chat"
    base_url: str = "https://api.deepseek.com"
    
    # Feature toggle
    enabled: bool = False
    
    # Generation parameters
    max_tokens: int = 8000
    temperature: float = 0.0
    timeout: int = 300 # seconds
    
    # Retry configuration
    max_retries: int = 0
    retry_delay: int = 2  # seconds
    
    # Cost/token tracking
    enable_token_tracking: bool = True
    
    class Config:
        env_file = ".env"
        env_prefix = "LLM_"
    
    def __init__(self, **kwargs):
        """Initialize configuration."""
        super().__init__(**kwargs)
        
        # If API key is not set, disable LLM
        if not self.api_key:
            self.enabled = False


# Global configuration instance
llm_config = LLMConfig()
