"""
Prompt Manager
Loads and manages AI prompts from YAML configuration
Supports hot-reloading for prompt updates without restart
"""
import yaml
from typing import Dict, Any
from pathlib import Path
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class PromptManager:
    """Manages AI prompts with hot-reload capability"""
    
    def __init__(self, prompts_path: str = None):
        self.prompts_path = Path(prompts_path or settings.PROMPTS_PATH)
        self._prompts_cache: Dict[str, Any] = {}
        self._load_prompts()
    
    def _load_prompts(self):
        """Load prompts from YAML file"""
        try:
            with open(self.prompts_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self._prompts_cache = data.get('prompts', {})
                logger.info(f"✅ Loaded {len(self._prompts_cache)} prompt templates")
                logger.info(f"📝 Prompts version: {data.get('version', 'unknown')}")
        except FileNotFoundError:
            logger.error(f"❌ Prompts file not found: {self.prompts_path}")
            self._prompts_cache = {}
        except yaml.YAMLError as e:
            logger.error(f"❌ Error parsing prompts YAML: {e}")
            self._prompts_cache = {}
    
    def reload(self):
        """Reload prompts from file (hot-reload)"""
        logger.info("🔄 Reloading prompts...")
        self._load_prompts()
    
    def get_prompt(self, prompt_name: str) -> Dict[str, Any]:
        """
        Get a prompt configuration by name
        
        Args:
            prompt_name: Name of the prompt (e.g., 'context_router')
        
        Returns:
            Dict with prompt configuration (template, temperature, etc.)
        """
        if prompt_name not in self._prompts_cache:
            logger.warning(f"⚠️  Prompt '{prompt_name}' not found, using fallback")
            return {
                "template": "You are a helpful assistant. User query: {user_input}",
                "temperature": 0.5,
                "max_tokens": 512
            }
        return self._prompts_cache[prompt_name]
    
    def format_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        Get formatted prompt with variables replaced
        
        Args:
            prompt_name: Name of the prompt
            **kwargs: Variables to replace in template (e.g., default_pincode="462001")
        
        Returns:
            Formatted prompt string
        """
        prompt_config = self.get_prompt(prompt_name)
        template = prompt_config.get('template', '')
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"❌ Missing variable in prompt template: {e}")
            return template
    
    def get_temperature(self, prompt_name: str) -> float:
        """Get temperature setting for a prompt"""
        return self.get_prompt(prompt_name).get('temperature', 0.5)
    
    def get_max_tokens(self, prompt_name: str) -> int:
        """Get max tokens setting for a prompt"""
        return self.get_prompt(prompt_name).get('max_tokens', 512)
    
    def list_prompts(self) -> list:
        """List all available prompt names"""
        return list(self._prompts_cache.keys())


# Global prompt manager instance
prompt_manager = PromptManager()
