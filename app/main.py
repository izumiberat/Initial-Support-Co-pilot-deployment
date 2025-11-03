import streamlit as st
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils import Config
from utils.rag_engine import RAGEngine
from utils.response_generator import ResponseGenerator
from utils.logger import logger

# Page configuration with professional theme
st.set_page_config(
    page_title="Support Co-pilot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2e86ab;
        margin-bottom: 1rem;
    }
    .response-box {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    .stButton button {
        width: 100%;
        border-radius: 0.5rem;
        font-weight: 500;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .footer {
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid #e9ecef;
        color: #6c757d;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize all session state variables"""
    default_states = {
        'conversation_history': [],
        'generated_response': "",
        'rag_engine': None,
        'response_generator': None,
        'sources': [],
        'last_issue': "",
        'system_initialized': False,
        'response_count': 0,
        'total_tokens_saved': 0  # Estimated based on response length
    }
    
    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value

def initialize_ai_components():
    """Initialize AI components with comprehensive error handling"""
    try:
        if st.session_state.rag_engine is None:
            with st.spinner("🔄 Connecting to AI services..."):
                st.session_state.rag_engine = RAGEngine()
        
        if st.session_state.response_generator is None:
            st.session_state.response_generator = ResponseGenerator()
        
        st.session_state.system_initialized = True
        logger.info("AI components initialized successfully")
        return True
        
    except Exception as e:
        error_msg = f"AI component initialization failed: {str(e)}"
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        st.info("💡 Please check your API keys and internet connection")
        return False

def index_sample_documents():
    """Index sample documents with progress tracking"""
    try:
        sample_docs_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'knowledge_base', 'sample_docs.txt')
        if os.path.exists(sample_docs_path):
            with st.spinner("📚 Indexing knowledge base..."):
                chunk_count = st.session_state.rag_engine.index_documents(sample_docs_path)
                logger.info(f"Indexed {chunk_count} documents successfully")
                return chunk_count
        else:
            warning_msg = "Sample documents not found - using general knowledge only"
            logger.warning(warning_msg)
            st.warning(f"📝 {warning_msg}")
            return 0
    except Exception as e:
        error_msg = f"Indexing failed: {str(e)}"
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        return 0

def render_sidebar():
    """Render the sidebar with configuration options"""
    with st.sidebar:
        st.markdown('<div class="sub-header">🔧 Configuration</div>', unsafe_allow_html=True)
        
        # System initialization
        if not st.session_state.system_initialized:
            if st.button("🚀 Initialize AI System", type="primary", use_container_width=True):
                if initialize_ai_components():
                    chunk_count = index_sample_documents()
                    if chunk_count > 0:
                        st.success(f"✅ System ready! Indexed {chunk_count} knowledge chunks")
                    else:
                        st.success("✅ System ready!")
        else:
            st.success("✅ AI System Initialized")
            
            if st.button("🔄 Reinitialize System", type="secondary", use_container_width=True):
                st.session_state.system_initialized = False
                st.session_state.rag_engine = None
                st.session_state.response_generator = None
                logger.info("System reinitialization triggered by user")
                st.rerun()
        
        st.markdown("---")
        
        # Response settings
        st.markdown('<div class="sub-header">🎛️ Response Settings</div>', unsafe_allow_html=True)
        
        tone_option = st.selectbox(
            "Response Tone:",
            ["empathetic", "professional", "reassuring", "formal", "friendly"],
            help="Choose the tone for generated responses"
        )
        
        context_sensitivity = st.slider(
            "Knowledge Base Usage:",
            min_value=1,
            max_value=5,
            value=3,
            help="How much to rely on knowledge base vs general knowledge"
        )
        
        st.markdown("---")
        
        # Metrics
        st.markdown('<div class="sub-header">📊 Metrics</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-card">Responses Generated: **{st.session_state.response_count}**</div>', unsafe_allow_html=True)
        
        estimated_savings = st.session_state.total_tokens_saved * 0.02  # Rough estimate
        st.markdown(f'<div class="metric-card">Time Saved: **~{estimated_savings:.1f} hours**</div>', unsafe_allow_html=True)
        
        return tone_option, context_sensitivity

def render_customer_input():
    """Render customer issue input section"""
    st.markdown('<div class="sub-header">📝 Customer Issue</div>', unsafe_allow_html=True)
    
    customer_issue = st.text_area(
        "Describe the customer's issue in detail:",
        height=150,
        placeholder="Example: Customer is frustrated because they can't login to their account and need to access important documents for an upcoming meeting. They've tried resetting password but didn't receive the email...",
        key="customer_issue_input",
        label_visibility="collapsed"
    )
    
    # Tone analysis
    if customer_issue and len(customer_issue) > 20 and st.session_state.response_generator:
        with st.spinner("🔍 Analyzing customer tone..."):
            try:
                detected_tone = st.session_state.response_generator.analyze_tone(customer_issue)
                tone_emojis = {
                    'frustrated': '😠', 
                    'urgent': '🚨', 
                    'calm': '😌', 
                    'confused': '😕', 
                    'neutral': '😐'
                }
                emoji = tone_emojis.get(detected_tone, '😐')
                st.info(f"{emoji} Detected tone: **{detected_tone.upper()}** - Response will be adjusted accordingly")
            except Exception as e:
                logger.warning(f"Tone analysis failed: {str(e)}")
                pass  # Silent fail for tone analysis
    
    return customer_issue

def render_response_output(tone_option, context_sensitivity, customer_issue):
    """Render response generation and display section"""
    st.markdown('<div class="sub-header">💡 Generated Response</div>', unsafe_allow_html=True)
    
    # Response display area
    if st.session_state.generated_response:
        # Use a text area for better display and easier copying
        st.text_area(
            "Response:",
            value=st.session_state.generated_response,
            height=300,
            key="response_display_area",
            label_visibility="collapsed"
        )
    else:
        st.markdown("""
        <div class="warning-box">
        <em>No response generated yet. Enter a customer issue and click "Generate Draft" to get started.</em>
        </div>
        """, unsafe_allow_html=True)
    
    # Action buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        generate_disabled = not customer_issue or not st.session_state.system_initialized
        if st.button("🎯 Generate Draft Response", type="primary", disabled=generate_disabled, use_container_width=True):
            with st.spinner("🧠 Analyzing issue and crafting response..."):
                try:
                    # Search for relevant context
                    context_chunks = st.session_state.rag_engine.search_similar(
                        customer_issue, 
                        top_k=context_sensitivity
                    )
                    
                    # Show context findings
                    if context_chunks:
                        st.success(f"📚 Found {len(context_chunks)} relevant knowledge base sections")
                    else:
                        st.warning("💡 No specific knowledge base matches - using general best practices")
                    
                    # Generate response with fallback
                    result = st.session_state.response_generator.generate_response_with_fallback(
                        customer_issue, 
                        context_chunks,
                        tone_option
                    )
                    
                    # Update session state
                    st.session_state.generated_response = result['response']
                    st.session_state.sources = result['sources']
                    st.session_state.last_issue = customer_issue
                    st.session_state.response_count += 1
                    st.session_state.total_tokens_saved += len(result['response'].split())  # Rough word count
                    
                    # Add to conversation history
                    st.session_state.conversation_history.insert(0, 
                        (customer_issue[:80] + "..." if len(customer_issue) > 80 else customer_issue,
                         result['response'][:100] + "..." if len(result['response']) > 100 else result['response'])
                    )
                    
                    # Log successful generation
                    logger.info(f"Successfully generated response #{st.session_state.response_count}")
                    
                    # Show success message
                    st.success("✅ Response generated successfully!")
                    
                    # Force refresh to show the new response
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    error_msg = f"Generation failed: {str(e)}"
                    logger.error(error_msg)
                    st.error(f"❌ {error_msg}")
    
    with col2:
        if st.session_state.generated_response:
            if st.button("📋 Copy Response", use_container_width=True):
                try:
                    # Try pyperclip first (more reliable)
                    import pyperclip
                    pyperclip.copy(st.session_state.generated_response)
                    st.success("✅ Response copied to clipboard!")
                    logger.info("Response copied to clipboard using pyperclip")
                except Exception as e:
                    # Fallback to JavaScript method
                    logger.warning(f"Pyperclip failed, using JS fallback: {str(e)}")
                    try:
                        # Escape the text for JavaScript
                        escaped_text = st.session_state.generated_response.replace('`', '\\`').replace('${', '\\${')
                        copy_js = f"""
                        <script>
                        function fallbackCopyTextToClipboard(text) {{
                            var textArea = document.createElement("textarea");
                            textArea.value = text;
                            textArea.style.position = "fixed";
                            textArea.style.left = "-999999px";
                            textArea.style.top = "-999999px";
                            document.body.appendChild(textArea);
                            textArea.focus();
                            textArea.select();
                            try {{
                                var successful = document.execCommand('copy');
                                console.log('Fallback copy ' + (successful ? 'successful' : 'unsuccessful'));
                            }} catch (err) {{
                                console.error('Fallback copy failed: ', err);
                            }}
                            document.body.removeChild(textArea);
                        }}
                        
                        function copyTextToClipboard(text) {{
                            if (!navigator.clipboard) {{
                                fallbackCopyTextToClipboard(text);
                                return;
                            }}
                            navigator.clipboard.writeText(text).then(function() {{
                                console.log('Clipboard copy successful');
                            }}, function(err) {{
                                console.error('Clipboard copy failed: ', err);
                                fallbackCopyTextToClipboard(text);
                            }});
                        }}
                        
                        copyTextToClipboard(`{escaped_text}`);
                        </script>
                        """
                        st.components.v1.html(copy_js, height=0)
                        st.success("✅ Response copied to clipboard!")
                    except Exception as js_error:
                        logger.error(f"JavaScript clipboard also failed: {str(js_error)}")
                        st.error("❌ Copy failed. Please select and copy the text manually.")
    
    with col3:
        if st.button("🔄 Clear All", use_container_width=True):
            st.session_state.generated_response = ""
            st.session_state.sources = []
            logger.info("UI cleared by user")
            st.rerun()
    
    # Sources section
    if st.session_state.sources:
        with st.expander("📚 Knowledge Base Sources Used", expanded=True):
            for i, source in enumerate(st.session_state.sources, 1):
                st.write(f"{i}. {source}")
                
def render_conversation_history():
    """Render conversation history section"""
    with st.expander("📋 Conversation History", expanded=False):
        if st.session_state.conversation_history:
            for i, (issue, response) in enumerate(st.session_state.conversation_history):
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write(f"**Case {i+1}:**")
                    st.write(issue)
                with col2:
                    st.write(f"**Response:**")
                    st.write(response)
                if i < len(st.session_state.conversation_history) - 1:
                    st.markdown("---")
        else:
            st.info("No conversation history yet. Generate some responses to see them here!")

def render_footer():
    """Render professional footer"""
    st.markdown("---")
    st.markdown('<div class="footer">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("""
        **Support Co-pilot** • AI-Powered Customer Support Drafting  
        *Reduce response time by 50%+ • Ensure accuracy with knowledge base*
        """)
    
    with col2:
        st.markdown("""
        **Built With:**  
        Streamlit • OpenAI GPT-4 • Pinecone
        """)
    
    with col3:
        estimated_hours_saved = st.session_state.total_tokens_saved * 0.02
        st.markdown("""
        **Performance:**  
        Responses Generated: **{:,}**  
        Time Saved: **~{:.1f} hours**
        """.format(st.session_state.response_count, estimated_hours_saved))
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    # Validate configuration first
    try:
        Config.validate()
        logger.info("Configuration validation successful")
    except ValueError as e:
        error_msg = f"Configuration error: {e}"
        logger.error(error_msg)
        st.error(f"❌ {error_msg}")
        st.info("🔧 Please check your .env file or set environment variables")
        return
    
    # Initialize session state
    initialize_session_state()
    
    # App header
    st.markdown('<div class="main-header">🤖 Support Co-pilot</div>', unsafe_allow_html=True)
    st.markdown("**AI-powered customer support response drafting** • *Reduce response time by 50%+*")
    
    st.markdown("---")
    
    # Render sidebar and get settings
    tone_option, context_sensitivity = render_sidebar()
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        customer_issue = render_customer_input()
    
    with col2:
        render_response_output(tone_option, context_sensitivity, customer_issue)
    
    # Conversation history
    render_conversation_history()
    
    # Footer
    render_footer()
    
    # Debug info (collapsed by default)
    with st.expander("🔧 Debug Information", expanded=False):
        st.write("Session State Keys:", list(st.session_state.keys()))
        st.write("System Initialized:", st.session_state.system_initialized)
        st.write("Response Count:", st.session_state.response_count)
        st.write("Total Tokens Saved:", st.session_state.total_tokens_saved)

if __name__ == "__main__":
    logger.info("Support Co-pilot application started")
    main()