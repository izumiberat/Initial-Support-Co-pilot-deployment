import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_environment():
    """Test that all environment variables are set"""
    load_dotenv()
    
    required_vars = ['OPENAI_API_KEY', 'PINECONE_API_KEY', 'PINECONE_ENVIRONMENT', 'PINECONE_INDEX_NAME']
    missing = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        return False
    else:
        print("✅ All environment variables are set")
        return True

def test_imports():
    """Test that all imports work correctly"""
    try:
        from utils import Config
        from utils.rag_engine import RAGEngine
        from utils.response_generator import ResponseGenerator
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_ai_components():
    """Test AI component initialization"""
    try:
        from utils.rag_engine import RAGEngine
        from utils.response_generator import ResponseGenerator
        
        # Test RAG engine
        rag = RAGEngine()
        print("✅ RAG engine initialized")
        
        # Test response generator
        generator = ResponseGenerator()
        print("✅ Response generator initialized")
        
        # Test basic search
        test_query = "login issues"
        results = rag.search_similar(test_query, top_k=1)
        print(f"✅ Search test: Found {len(results)} results")
        
        return True
        
    except Exception as e:
        print(f"❌ AI components test failed: {e}")
        return False

def test_knowledge_base():
    """Test knowledge base indexing"""
    try:
        from utils.rag_engine import RAGEngine
        
        rag = RAGEngine()
        sample_docs_path = os.path.join('data', 'knowledge_base', 'sample_docs.txt')
        
        if os.path.exists(sample_docs_path):
            chunk_count = rag.index_documents(sample_docs_path)
            print(f"✅ Knowledge base indexed: {chunk_count} chunks")
            return True
        else:
            print("⚠️ Sample knowledge base file not found")
            return True  # Not a critical failure
            
    except Exception as e:
        print(f"❌ Knowledge base test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🧪 Running Support Co-pilot Tests...")
    print("=" * 50)
    
    tests = [
        test_environment,
        test_imports,
        test_ai_components,
        test_knowledge_base
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All tests passed! ({passed}/{total})")
        return True
    else:
        print(f"⚠️  Some tests failed: ({passed}/{total})")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)