import os
from pinecone import Pinecone, ServerlessSpec  # UPDATED IMPORT
from dotenv import load_dotenv

load_dotenv()

def create_pinecone_index():
    """Create and configure the Pinecone index for our support co-pilot"""
    
    pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
    
    index_name = "support-knowledge-base"
    
    # Check if index exists
    if index_name not in pc.list_indexes().names():
        print(f"Creating index: {index_name}")
        
        pc.create_index(
            name=index_name,
            dimension=1536,  # OpenAI text-embedding-3-small dimension
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",  # or "gcp" based on your preference
                region="us-east-1"
            )
        )
        
        print("✅ Index created successfully!")
        
        # Wait for index to be ready
        print("🕐 Waiting for index to be ready...")
        while not pc.describe_index(index_name).status['ready']:
            pass
            
        print("✅ Index is ready!")
    else:
        print("✅ Index already exists!")

if __name__ == "__main__":
    create_pinecone_index()