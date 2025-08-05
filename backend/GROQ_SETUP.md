# Groq API Setup Guide

## Overview
This project now uses Groq API with the Mixtral-8x7b-32768 model instead of local Ollama. This provides faster, more reliable AI responses.

## Setup Steps

### 1. Get Groq API Key
1. Go to [Groq Console](https://console.groq.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the API key

### 2. Configure Environment Variables
Create a `.env` file in the `backend` directory with:

```env
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/
DATABASE_NAME=documents
COLLECTION_NAME=mangobytes

# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Test the Setup
Run the test script to verify everything works:

```bash
cd backend
python test_groq.py
```

### 4. Start the Application
Use the updated start script:

```bash
./start_all.bat
```

## Benefits of Groq API

- **Faster Responses**: Groq's infrastructure is optimized for speed
- **No Local Setup**: No need to install or manage Ollama locally
- **Better Reliability**: Cloud-based service with high uptime
- **Mixtral Model**: Uses the powerful Mixtral-8x7b-32768 model
- **Cost Effective**: Pay-per-use pricing model

## Model Details

- **Model**: llama3-70b-8192
- **Context Length**: 8,192 tokens
- **Speed**: Optimized for fast inference
- **Quality**: High-quality responses for summarization, RAG, and comparison

## Troubleshooting

### API Key Issues
- Ensure your API key is correctly set in `.env`
- Check that the key has sufficient credits
- Verify the key is active in Groq console

### Connection Issues
- Check your internet connection
- Verify Groq API is accessible from your location
- Try running `python test_groq.py` to diagnose issues

### Performance Issues
- The system includes fallback mechanisms if Groq API fails
- Check the console logs for detailed error messages
- Ensure MongoDB is running for document storage 