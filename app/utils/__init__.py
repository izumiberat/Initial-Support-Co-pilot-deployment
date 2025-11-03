import os
import streamlit as st
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv()

class Config:
    """Central configuration management that works for both local and Streamlit Cloud"""
    
    @staticmethod
    def _get_secret(key):
        """Get secret from Streamlit secrets or fall back to environment variable"""
        try:
            # Try Streamlit secrets first (for cloud deployment)
            if hasattr(st, 'secrets') and key in st.secrets:
                return st.secrets[key]
            # Fall back to environment variables (for local development)
            return os.getenv(key)
        except Exception:
            return os.getenv(key)
    
    # API Keys
    @property
    def OPENAI_API_KEY(self):
        return self._get_secret('OPENAI_API_KEY')
    
    @property
    def PINECONE_API_KEY(self):
        return self._get_secret('PINECONE_API_KEY')
    
    # Pinecone Configuration
    @property
    def PINECONE_ENVIRONMENT(self):
        return self._get_secret('PINECONE_ENVIRONMENT') or 'us-east-1-aws'
    
    @property
    def PINECONE_INDEX_NAME(self):
        return self._get_secret('PINECONE_INDEX_NAME') or 'support-knowledge-base'
    
    @classmethod
    def validate(cls):
        """Ensure all required environment variables are set"""
        config = cls()
        required_vars = ['OPENAI_API_KEY', 'PINECONE_API_KEY']
        missing = []
        
        for var in required_vars:
            value = getattr(config, var)
            if not value:
                missing.append(var)
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True

# Create a global instance
config = Config()