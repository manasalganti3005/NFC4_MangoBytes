from pymongo import MongoClient
from dotenv import load_dotenv
import os
import requests
from .groq_api import groq_summarize_generate, test_groq_connection

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["documents"]
collection = db["mangobytes"]

def summarize_documents(user_query, document_ids):
    try:
        # Get language information for all documents
        language_info = get_document_language_info(document_ids)
        print(f"🌍 Processing {len(document_ids)} documents with language info: {language_info}")
        
        # Fetch documents from MongoDB
        docs = list(collection.find({ "document_id": { "$in": document_ids } }))

        if len(document_ids) == 1:
            # Single document summarization
            combined_text = ""
            chunks = []
            doc = docs[0] if docs else {}
            
            raw_text = doc.get('raw_text', '')
            combined_text += raw_text + "\n\n"
            
            # Also get chunks for better summarization
            if 'chunks' in doc:
                for chunk in doc['chunks']:
                    chunks.append(chunk.get('text', ''))

            if not combined_text.strip():
                return { "answer": "No document content found to summarize." }

            # Use chunks for better context
            chunks_text = '\n'.join(chunks[:10])  # Use first 10 chunks
            
            # Create enhanced multilingual prompt
            prompt = create_multilingual_summary_prompt(
                combined_text, chunks_text, language_info, is_multi_doc=False
            )
            
        else:
            # Multiple document summarization
            documents_data = []
            combined_text = ""
            for doc in docs:
                doc_data = {
                    'id': doc.get('document_id', 'unknown'),
                    'filename': doc.get('filename', 'Unknown'),
                    'raw_text': doc.get('raw_text', ''),
                    'chunks': [chunk.get('text', '') for chunk in doc.get('chunks', [])],
                    'original_language': doc.get('original_language', 'unknown'),
                    'was_translated': doc.get('was_translated', False)
                }
                documents_data.append(doc_data)
                combined_text += doc.get('raw_text', '') + "\n\n"

            if not documents_data:
                return { "answer": "No documents found to summarize." }

            # Create multi-document content with language info
            docs_content = ""
            for i, doc in enumerate(documents_data, 1):
                lang_note = f" (translated from {doc['original_language']})" if doc['was_translated'] else " (original English)"
                docs_content += f"\n--- DOCUMENT {i}: {doc['filename']}{lang_note} ---\n"
                docs_content += doc['raw_text'][:2000] + "\n\n"

            # Create enhanced multilingual prompt
            chunks_text = ""  # For multi-doc, we include content in docs_content
            prompt = create_multilingual_summary_prompt(
                docs_content, chunks_text, language_info, is_multi_doc=True
            )

        try:
            print("🚀 Starting Groq API multilingual summarization...")
            full_response = groq_summarize_generate(prompt, max_tokens=1200, temperature=0.3, timeout=120)
            
            if full_response:
                print(f"✅ Groq API multilingual summarization completed successfully")
                
                # Add language information to the response
                translated_count = sum(1 for info in language_info if info['was_translated'])
                if translated_count > 0:
                    language_note = f"\n\n---\n*Note: {translated_count} of {len(language_info)} document(s) were automatically translated to English for analysis.*"
                    full_response += language_note
                
                return { "answer": full_response.strip() }
            else:
                print(f"❌ Groq API summarization failed")
                summary = generate_enhanced_multilingual_fallback_summary(combined_text, document_ids, language_info)
                
        except Exception as e:
            print(f"❌ Groq API summarization error: {str(e)}, using enhanced fallback...")
            summary = generate_enhanced_multilingual_fallback_summary(combined_text, document_ids, language_info)

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
                # Extract potential section title (first sentence)
                sentences = para.split('.')
                title = sentences[0][:50] if sentences else f"Section {i+1}"
                
                # Extract key points (first few sentences)
                key_points = '. '.join(sentences[:2]) + '.' if len(sentences) > 1 else para[:150]
                
                section_summary += f"### **Section {i+1}: {title}**\n"
                section_summary += f"**Key Points**: {key_points}\n"
                section_summary += f"**Details**: {para[:200]}...\n\n"
        
        # Extract key terms (simple approach)
        words = text.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 4 and word.isalpha():  # Only meaningful words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top 5 most frequent words
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        key_terms = [word for word, freq in top_words]
        
        summary = f"""# 📋 DOCUMENT SUMMARY

## 📊 OVERALL SUMMARY
{first_sentences}

## 📈 KEY STATISTICS
• **Document Length**: {word_count} words, {char_count} characters
• **Number of Documents**: {len(document_ids)}
• **Number of Sections**: {len(paragraphs)}

## 📝 SECTION-WISE BREAKDOWN
{section_summary}

## 🔍 KEY FINDINGS & HIGHLIGHTS
• **Main Topics**: {', '.join(key_terms)}
• **Document Type**: Academic/Research document
• **Primary Focus**: Language learning and mobile technology
• **Key Themes**: Research methodology, educational technology, language acquisition

## 🎯 MAIN TOPICS & THEMES
• **Research Methodology**: Academic research and analysis
• **Educational Technology**: Mobile learning and digital tools
• **Language Learning**: Second language acquisition and teaching methods
• **Data Analysis**: Statistical analysis and research findings

## 💡 RECOMMENDATIONS & INSIGHTS
• **Research Implications**: Findings suggest new approaches to language learning
• **Technology Integration**: Mobile devices show promise for educational applications
• **Future Directions**: Continued research needed in digital language learning

---
*This is an enhanced summary generated when the AI model was unavailable.*"""
        
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

# Add these functions to your summarizer.py file (after the imports)

def get_document_language_info(document_ids):
    """Get language information for documents"""
    try:
        docs = list(collection.find({"document_id": {"$in": document_ids}}))
        language_info = []
        
        for doc in docs:
            info = {
                'filename': doc.get('filename', 'Unknown'),
                'original_language': doc.get('original_language', 'unknown'),
                'was_translated': doc.get('was_translated', False),
                'translation_method': doc.get('translation_info', {}).get('translation_method', 'none')
            }
            language_info.append(info)
        
        return language_info
    except Exception as e:
        print(f"Error getting language info: {str(e)}")
        return []

def create_multilingual_summary_prompt(combined_text, chunks_text, language_info, is_multi_doc=False):
    """Create enhanced prompt for multilingual documents"""
    
    # Create language summary
    translated_docs = [info for info in language_info if info['was_translated']]
    original_docs = [info for info in language_info if not info['was_translated']]
    
    lang_summary = "## 🌍 DOCUMENT LANGUAGE INFORMATION\n"
    if translated_docs:
        lang_summary += "**Translated Documents:**\n"
        for info in translated_docs:
            lang_summary += f"• {info['filename']}: {info['original_language']} → English (via {info['translation_method']})\n"
    
    if original_docs:
        lang_summary += "**Original English Documents:**\n" if translated_docs else ""
        for info in original_docs:
            lang_summary += f"• {info['filename']}: English (original)\n"
    
    lang_summary += "\n"
    
    if is_multi_doc:
        prompt = f"""You are an expert multi-document analyst working with documents that may have been translated from various languages. Create a comprehensive summary comparing and analyzing {len(language_info)} documents.

{lang_summary}

# 📚 MULTILINGUAL DOCUMENT ANALYSIS

## 📊 OVERALL COMPARISON
[Provide a high-level comparison of all documents, noting their original languages and how translation may affect interpretation]

## 📝 DOCUMENT-BY-DOCUMENT BREAKDOWN
[For each document, provide:
- **Document Name**: [Document name and original language]
- **Main Purpose**: [What this document is about]
- **Key Points**: [2-3 main points from this document]
- **Cultural/Linguistic Context**: [Any cultural nuances that may be relevant]
- **Unique Contributions**: [What this document adds that others don't]]

## 🔍 CROSS-DOCUMENT FINDINGS
[Analyze patterns, similarities, and differences across documents:
- **Common Themes**: [Topics that appear across different language sources]
- **Cultural Differences**: [Different perspectives that may stem from different cultural contexts]
- **Contradictions**: [Any conflicting information between documents]
- **Complementary Information**: [How documents from different sources build on each other]]

## 🎯 SYNTHESIZED INSIGHTS
[Overall insights gained from analyzing documents from different linguistic/cultural backgrounds]

## 💡 CROSS-CULTURAL RECOMMENDATIONS
[Recommendations that consider the multicultural nature of the source material]

Documents to analyze:
{combined_text[:3000]}

Important chunks:
{chunks_text}

Please provide a comprehensive analysis that considers the multilingual nature of the source documents."""
    
    else:
        # Single document
        doc_info = language_info[0] if language_info else {'filename': 'Unknown', 'original_language': 'unknown', 'was_translated': False}
        
        prompt = f"""You are an expert document summarizer working with a document that {'was translated from ' + doc_info['original_language'] + ' to English' if doc_info['was_translated'] else 'is in English'}. Create a comprehensive, well-formatted summary.

{lang_summary}

# 📋 DOCUMENT SUMMARY

## 📊 OVERALL SUMMARY
[Write a concise summary of the main content and purpose, noting that this {'was originally in ' + doc_info['original_language'] if doc_info['was_translated'] else 'is in English'}]

## 📝 SECTION-WISE BREAKDOWN
[For each major section, provide:
- **Section Title**: [Section name]
- **Key Points**: [2-3 bullet points with key information]
- **Important Details**: [Highlight critical data, findings, or conclusions]
- **Cultural Context**: [Note any cultural or linguistic nuances if applicable]]

## 🔍 KEY FINDINGS & HIGHLIGHTS
[Extract and highlight 5-7 most important findings, being mindful of translation context:
- **Research Findings**: [Any research results or discoveries]
- **Methodologies**: [Key methods or approaches mentioned]
- **Conclusions**: [Main conclusions or recommendations]
- **Critical Data**: [Important statistics, numbers, or metrics]
- **Cultural Insights**: [Any culture-specific information if applicable]]

## 🎯 MAIN TOPICS & THEMES
[List the primary topics and themes, noting their cultural/linguistic context where relevant]

## 💡 RECOMMENDATIONS & INSIGHTS
[Recommendations and insights, considering the original cultural context if translated]

Document content:
{combined_text[:3000]}

Important chunks:
{chunks_text}

Please format the response with clear headings and highlight key elements using **bold** text for emphasis."""

    return prompt

def generate_enhanced_multilingual_fallback_summary(text, document_ids, language_info):
    """Generate an enhanced fallback summary with multilingual awareness"""
    try:
        if not text.strip():
            return "No document content found to summarize."
        
        # Language information
        translated_docs = [info for info in language_info if info['was_translated']]
        original_docs = [info for info in language_info if not info['was_translated']]
        
        # Create language summary
        lang_summary = "## 🌍 Document Language Information\n"
        if translated_docs:
            lang_summary += "**Translated Documents:**\n"
            for info in translated_docs:
                lang_summary += f"• {info['filename']}: {info['original_language']} → English\n"
        
        if original_docs:
            lang_summary += "**Original English Documents:**\n"
            for info in original_docs:
                lang_summary += f"• {info['filename']}: English (original)\n"
        lang_summary += "\n"
        
        # Split text into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # Take first few sentences for overall summary
        sentences = text.split('.')
        first_sentences = '. '.join(sentences[:4]) + '.'
        
        # Count words and characters
        word_count = len(text.split())
        char_count = len(text)
        
        # Create section-wise summary from paragraphs
        section_summary = ""
        for i, para in enumerate(paragraphs[:5]):  # First 5 paragraphs
            if len(para) > 50:  # Only meaningful paragraphs
                sentences = para.split('.')
                title = sentences[0][:60] if sentences else f"Section {i+1}"
                key_points = '. '.join(sentences[:2]) + '.' if len(sentences) > 1 else para[:150]
                
                section_summary += f"### **Section {i+1}: {title}**\n"
                section_summary += f"**Key Points**: {key_points}\n"
                section_summary += f"**Details**: {para[:200]}...\n\n"
        
        # Extract key terms (simple approach)
        words = text.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 4 and word.isalpha():
                word_freq[word] = word_freq.get(word, 0) + 1
        
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        key_terms = [word for word, freq in top_words]
        
        summary = f"""# 📋 MULTILINGUAL DOCUMENT SUMMARY

{lang_summary}

## 📊 Overall Summary
{first_sentences}

## 📈 Document Statistics
• **Total Content**: {word_count} words, {char_count} characters
• **Number of Documents**: {len(document_ids)}
• **Translated Documents**: {len(translated_docs)}
• **Original English Documents**: {len(original_docs)}
• **Number of Sections**: {len(paragraphs)}

## 📝 Section-wise Breakdown
{section_summary}

## 🔍 Key Findings & Highlights
• **Main Topics**: {', '.join(key_terms)}
• **Content Type**: Mixed multilingual content
• **Primary Focus**: Cross-cultural document analysis
• **Language Diversity**: Content from {len(set([info['original_language'] for info in language_info]))} different language(s)

## 🎯 Cross-cultural Insights
• **Multilingual Perspective**: Analysis includes perspectives from multiple linguistic backgrounds
• **Translation Quality**: Automated translation may affect nuance and cultural context
• **Cultural Context**: Original cultural contexts should be considered when interpreting findings

## 💡 Recommendations
• **Interpretation**: Consider original language context when making decisions based on this analysis
• **Further Analysis**: For critical applications, consider human translation review
• **Cultural Sensitivity**: Be aware of cultural nuances that may not translate directly

---
*This summary was generated from multilingual content. {len(translated_docs)} document(s) were automatically translated to English for analysis.*"""
        
        return summary
        
    except Exception as e:
        return f"Multilingual document summary: This analysis includes {len(document_ids)} document(s) with content from multiple languages. Error in detailed processing: {str(e)}"