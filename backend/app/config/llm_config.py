import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv, find_dotenv


# Get the directory of this config file
config_dir = Path(__file__).parent.parent.parent
os.chdir(config_dir)

# Try to find .env in the backend directory
env_path = config_dir / "backend" / ".env"
if env_path.exists():
    load_dotenv(env_path)
elif not find_dotenv():
    pass  # No .env file - continue without it
else:
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
