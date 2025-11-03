import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Central configuration management"""
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
    
    @classmethod
    def validate(cls):
        """Ensure all required environment variables are set"""
        required_vars = ['OPENAI_API_KEY', 'PINECONE_API_KEY']
        missing = [var for var in required_vars if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")