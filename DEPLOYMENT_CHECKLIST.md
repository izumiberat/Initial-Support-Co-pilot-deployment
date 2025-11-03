# Support Co-pilot Deployment Checklist

## Pre-Deployment
- [ ] All tests pass (`python test_support_copilot.py`)
- [ ] Environment variables set in Streamlit Cloud
- [ ] Knowledge base documents are properly formatted
- [ ] Pinecone index is created and accessible
- [ ] API rate limits are understood and handled

## Streamlit Cloud Deployment
1. Push code to GitHub repository
2. Go to [Streamlit Community Cloud](https://share.streamlit.io/)
3. Click "New app"
4. Select your repository, branch, and main file path (`app/main.py`)
5. Set advanced settings:
   - Python version: 3.9+
   - Add environment variables

## Environment Variables for Streamlit Cloud
OPENAI_API_KEY=your_key_here
PINECONE_API_KEY=your_key_here
PINECONE_ENVIRONMENT=your_environment
PINECONE_INDEX_NAME=support-knowledge-base


## Post-Deployment Verification
- [ ] App loads without errors
- [ ] AI system initializes successfully
- [ ] Response generation works
- [ ] Knowledge base search functions
- [ ] UI is responsive and professional