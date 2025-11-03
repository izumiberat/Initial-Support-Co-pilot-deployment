import os
import openai
from pinecone import Pinecone, ServerlessSpec
from utils import config
from utils.logger import logger
import tiktoken
from typing import List, Dict, Optional
import re
import time

class RAGEngine:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
        self.pc = Pinecone(api_key=config.PINECONE_API_KEY)
        self.index = self._initialize_index()
        self.embedding_model = "text-embedding-3-small"
        logger.info("RAG Engine initialized successfully")
        
    def _initialize_index(self) -> Pinecone.Index:
        """Initialize and validate the Pinecone index"""
        try:
            # Check if index exists
            if config.PINECONE_INDEX_NAME not in self.pc.list_indexes().names():
                error_msg = f"Index '{config.PINECONE_INDEX_NAME}' not found. Please create it first."
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            index = self.pc.Index(config.PINECONE_INDEX_NAME)
            
            # Test the connection
            index_stats = index.describe_index_stats()
            logger.info(f"Connected to Pinecone index: {config.PINECONE_INDEX_NAME}")
            logger.info(f"Index stats: {index_stats.total_vector_count} vectors")
            
            return index
            
        except Exception as e:
            error_msg = f"Pinecone initialization failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embeddings for text using OpenAI"""
        try:
            # Clean and prepare text
            clean_text = text.replace("\n", " ").strip()
            if not clean_text:
                raise ValueError("Text cannot be empty")
                
            response = self.openai_client.embeddings.create(
                input=[clean_text],
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            error_msg = f"Embedding generation failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def smart_chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Smart text chunking that respects sentence boundaries"""
        try:
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Split by sections first (marked with [Section Name])
            sections = re.split(r'(\[.*?\])', text)
            chunks = []
            
            for section in sections:
                if not section.strip():
                    continue
                    
                # If it's a section header, keep it with content
                if section.startswith('[') and section.endswith(']'):
                    current_chunk = section
                else:
                    # Split remaining text by sentences
                    sentences = re.split(r'(?<=[.!?])\s+', section)
                    current_chunk = ""
                    
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) <= chunk_size:
                            current_chunk += " " + sentence if current_chunk else sentence
                        else:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = sentence
                    
                    if current_chunk:
                        chunks.append(current_chunk.strip())
            
            filtered_chunks = [chunk for chunk in chunks if chunk and len(chunk) > 10]
            logger.debug(f"Created {len(filtered_chunks)} chunks from text")
            return filtered_chunks
            
        except Exception as e:
            logger.error(f"Text chunking failed: {str(e)}")
            return []
    
    def index_documents(self, file_path: str) -> int:
        """Index documents from a file with smart chunking"""
        try:
            if not os.path.exists(file_path):
                error_msg = f"Knowledge base file not found: {file_path}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                error_msg = "Knowledge base file is empty"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            chunks = self.smart_chunk_text(content)
            
            if not chunks:
                error_msg = "No valid chunks created from the knowledge base"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.info(f"Created {len(chunks)} chunks from knowledge base")
            
            vectors = []
            for i, chunk in enumerate(chunks):
                embedding = self.get_embedding(chunk)
                vectors.append({
                    'id': f"chunk_{i}_{int(time.time())}",
                    'values': embedding,
                    'metadata': {
                        'text': chunk, 
                        'chunk_id': i,
                        'source': os.path.basename(file_path)
                    }
                })
            
            # Upsert in batches for better performance
            batch_size = 100
            successful_uploads = 0
            
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                try:
                    self.index.upsert(vectors=batch)
                    successful_uploads += len(batch)
                    logger.info(f"Uploaded batch {i//batch_size + 1}/{(len(vectors)-1)//batch_size + 1}")
                except Exception as e:
                    logger.warning(f"Failed to upload batch {i//batch_size + 1}: {str(e)}")
                    # Try individual uploads for the failed batch
                    for vector in batch:
                        try:
                            self.index.upsert(vectors=[vector])
                            successful_uploads += 1
                        except Exception:
                            continue
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            logger.info(f"Successfully uploaded {successful_uploads}/{len(vectors)} vectors")
            return successful_uploads
            
        except Exception as e:
            error_msg = f"Document indexing failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def search_similar(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search for similar content using semantic search"""
        try:
            if not query or not query.strip():
                logger.warning("Empty query provided to search_similar")
                return []
                
            if not hasattr(self, 'index') or self.index is None:
                logger.error("Pinecone index not initialized")
                return []
                
            query_embedding = self.get_embedding(query)
            
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            # Filter and format results
            formatted_results = []
            for match in results.matches:
                if match.score > 0.5:  # Only use relevant matches
                    formatted_results.append({
                        'text': match.metadata['text'],
                        'score': match.score,
                        'chunk_id': match.metadata['chunk_id'],
                        'source': match.metadata.get('source', 'unknown')
                    })
            
            logger.info(f"Found {len(formatted_results)} relevant knowledge base matches for query: '{query[:50]}...'")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []