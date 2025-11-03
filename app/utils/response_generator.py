import openai
from utils import Config
from utils.logger import logger
from typing import List, Dict
import json
import time

class ResponseGenerator:
    def __init__(self):
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = "gpt-4"
        logger.info("Response Generator initialized with GPT-4")
    
    def generate_response(self, customer_issue: str, context_chunks: List[Dict], tone: str = "empathetic") -> Dict:
        """Generate a support response using context and specified tone"""
        try:
            # Build context from retrieved chunks
            context_text = "\n\n".join([chunk['text'] for chunk in context_chunks])
            
            # System prompt that defines the AI's role and behavior
            system_prompt = """You are an expert customer support agent. Your role is to draft helpful, accurate, and professional responses to customer issues.

KEY INSTRUCTIONS:
1. Use the provided knowledge base context to ensure accuracy
2. Always maintain an empathetic and professional tone
3. If the context doesn't contain the answer, be honest and offer to escalate
4. Structure responses clearly with proper formatting
5. Reference specific policies or solutions when available
6. Always thank the customer for their patience

CRITICAL: Do not make up information outside the provided context."""
            
            # User prompt with structured input
            user_prompt = f"""
CUSTOMER ISSUE:
{customer_issue}

RELEVANT KNOWLEDGE BASE CONTEXT:
{context_text}

TONE REQUIREMENT: {tone}

Please draft a response that:
- Acknowledges the specific issue
- Provides solutions based on the knowledge base
- Shows empathy for their situation
- Maintains professional brand voice
- Includes clear next steps if needed

DRAFT YOUR RESPONSE:"""
            
            logger.info(f"Generating response for issue: '{customer_issue[:100]}...' with {len(context_chunks)} context chunks")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            generated_text = response.choices[0].message.content
            
            # Extract sources for transparency
            sources = [f"Knowledge base chunk {chunk['chunk_id']} (score: {chunk['score']:.2f})" 
                      for chunk in context_chunks]
            
            logger.info(f"Successfully generated response using {len(context_chunks)} context chunks")
            
            return {
                'response': generated_text,
                'sources': sources,
                'context_used': len(context_chunks),
                'model_used': self.model
            }
            
        except openai.APIError as e:
            error_msg = f"OpenAI API error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Response generation failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def analyze_tone(self, customer_message: str) -> str:
        """Analyze customer message tone to adapt response style"""
        try:
            logger.debug(f"Analyzing tone for message: '{customer_message[:50]}...'")
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Analyze the emotional tone of this customer message. Respond with ONLY one word: 'frustrated', 'urgent', 'calm', 'confused', or 'neutral'."},
                    {"role": "user", "content": customer_message}
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            tone = response.choices[0].message.content.strip().lower()
            valid_tones = ['frustrated', 'urgent', 'calm', 'confused', 'neutral']
            
            detected_tone = tone if tone in valid_tones else 'neutral'
            logger.debug(f"Detected tone: {detected_tone}")
            
            return detected_tone
            
        except Exception as e:
            logger.warning(f"Tone analysis failed, using neutral: {str(e)}")
            return 'neutral'

    def generate_response_with_fallback(self, customer_issue: str, context_chunks: List[Dict], tone: str = "empathetic") -> Dict:
        """Generate response with comprehensive error handling and fallbacks"""
        max_retries = 2
        last_error = None
        
        logger.info(f"Attempting response generation with fallback for: '{customer_issue[:50]}...'")
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Generation attempt {attempt + 1}/{max_retries}")
                return self.generate_response(customer_issue, context_chunks, tone)
            except openai.RateLimitError as e:
                last_error = f"OpenAI rate limit exceeded: {str(e)}"
                logger.warning(f"Rate limit hit, attempt {attempt + 1}: {last_error}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
            except openai.APIConnectionError as e:
                last_error = f"OpenAI connection error: {str(e)}"
                logger.warning(f"Connection error, attempt {attempt + 1}: {last_error}")
                if attempt < max_retries - 1:
                    time.sleep(1)
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.error(f"Unexpected error in attempt {attempt + 1}: {last_error}")
                break
        
        # Fallback response if all retries fail
        logger.error(f"All generation attempts failed, using fallback response. Last error: {last_error}")
        return {
            'response': f"I apologize, but I'm experiencing technical difficulties. Please try again in a moment. For immediate assistance, you can refer to our knowledge base or contact support directly.\n\nError: {last_error}",
            'sources': [],
            'context_used': 0,
            'model_used': 'fallback'
        }