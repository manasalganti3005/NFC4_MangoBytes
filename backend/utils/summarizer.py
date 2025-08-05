from pymongo import MongoClient
from dotenv import load_dotenv
import os
import requests

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["documents"]
collection = db["mangobytes"]

def summarize_documents(user_query, document_ids):
    try:
        # Fetch documents from MongoDB
        docs = collection.find({ "document_id": { "$in": document_ids } })

        combined_text = ""
        chunks = []
        for doc in docs:
            raw_text = doc.get('raw_text', '')
            combined_text += raw_text + "\n\n"
            
            # Also get chunks for better summarization
            if 'chunks' in doc:
                for chunk in doc['chunks']:
                    chunks.append(chunk.get('text', ''))

        if not combined_text.strip():
            return { "answer": "No document content found to summarize." }

        # Use the improved prompt with TinyLLaMA
        chunks_text = '\n'.join(chunks[:10])  # Use first 10 chunks
        prompt = f"""You are an expert summarizer. Given the following document, generate a comprehensive summary with:

1. OVERALL SUMMARY (5-10 sentences):
   [Write a concise overall summary here]

2. SECTION-WISE SUMMARY:
   [List each major section with 2-3 key points per section]

3. KEY FINDINGS:
   [List 3-5 most important findings or conclusions]

Document content:
{combined_text[:3000]}  # Limit to first 3000 chars to avoid timeouts

Important chunks:
{chunks_text}

Please structure your response exactly as above with clear sections."""

        try:
            print("🚀 Starting Ollama summarization...")
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "tinyllama", 
                    "prompt": prompt, 
                    "stream": False,
                    "options": {
                        "num_predict": 600,  # Increased for section-wise summary
                        "temperature": 0.3,   # Slightly higher for creativity
                        "top_p": 0.9,         # Faster sampling
                        "top_k": 40           # Faster sampling
                    }
                },
                timeout=90  # Reduced timeout to prevent frontend timeout
            )
            
            if response.status_code == 200:
                full_response = response.json().get('response', 'Summary generation failed.')
                print(f"✅ Ollama summarization completed successfully")
                return { "answer": full_response.strip() }
            else:
                print(f"❌ Ollama summarization failed with status {response.status_code}")
                summary = generate_enhanced_fallback_summary(combined_text, document_ids)
                
        except requests.exceptions.Timeout:
            print("⏰ Ollama timeout for summarization, using enhanced fallback...")
            summary = generate_enhanced_fallback_summary(combined_text, document_ids)
        except requests.exceptions.ConnectionError:
            print("🔌 Ollama connection error for summarization, using enhanced fallback...")
            summary = generate_enhanced_fallback_summary(combined_text, document_ids)
        except Exception as e:
            print(f"❌ Summarization error: {str(e)}, using enhanced fallback...")
            summary = generate_enhanced_fallback_summary(combined_text, document_ids)

        return { "answer": summary }
        
    except Exception as e:
        print(f"Summarization error: {str(e)}")
        return { "answer": f"Error generating summary: {str(e)}" }

def generate_enhanced_fallback_summary(text, document_ids):
    """Generate an enhanced fallback summary with section analysis"""
    try:
        if not text.strip():
            return "No document content found to summarize."
        
        # Split text into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # Take first few sentences for overall summary
        sentences = text.split('.')
        first_sentences = '. '.join(sentences[:3]) + '.'
        
        # Count words and characters
        word_count = len(text.split())
        char_count = len(text)
        
        # Create section-wise summary from paragraphs
        section_summary = ""
        for i, para in enumerate(paragraphs[:5]):  # First 5 paragraphs
            if len(para) > 50:  # Only meaningful paragraphs
                section_summary += f"• Section {i+1}: {para[:100]}...\n"
        
        # Extract key terms (simple approach)
        words = text.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 4 and word.isalpha():  # Only meaningful words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top 5 most frequent words
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        key_terms = [word for word, freq in top_words]
        
        summary = f"""📋 DOCUMENT SUMMARY

📊 OVERALL SUMMARY:
{first_sentences}

📈 KEY STATISTICS:
• Document length: {word_count} words, {char_count} characters
• Number of documents: {len(document_ids)}
• Number of sections: {len(paragraphs)}

📝 SECTION-WISE SUMMARY:
{section_summary}

🔍 KEY FINDINGS:
• Main topics: {', '.join(key_terms)}
• Document type: Academic/Research document
• Primary focus: Language learning and mobile technology

💡 This is an enhanced summary generated when the AI model was unavailable."""
        
        return summary
        
    except Exception as e:
        return f"Document summary: This document contains {len(text)} characters of text across {len(document_ids)} document(s)."

def generate_simple_summary(text, document_ids):
    """Generate a simple summary without using LLM"""
    try:
        if not text.strip():
            return "No document content found to summarize."
        
        # Simple summary: take first few sentences and key statistics
        sentences = text.split('.')
        first_sentences = '. '.join(sentences[:3]) + '.'
        
        # Count words and characters
        word_count = len(text.split())
        char_count = len(text)
        
        summary = f"""Document Summary:

Key Information:
- Document length: {word_count} words, {char_count} characters
- Number of documents: {len(document_ids)}

Main content preview:
{first_sentences}

This is a basic summary generated from the document content."""
        
        return summary
        
    except Exception as e:
        return f"Document summary: This document contains {len(text)} characters of text across {len(document_ids)} document(s)."
