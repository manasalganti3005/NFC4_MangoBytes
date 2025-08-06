import os
import requests
from dotenv import load_dotenv
from .groq_api import groq_generate
import re
from googletrans import Translator
import langdetect

load_dotenv()

# Initialize Google Translator as fallback
google_translator = Translator()

def detect_language(text):
    """
    Detect the language of the given text
    Returns: language code (e.g., 'es', 'fr', 'de', 'hi', etc.)
    """
    try:
        # Try langdetect first (more reliable for longer texts)
        detected = langdetect.detect(text[:1000])  # Use first 1000 chars for detection
        confidence = langdetect.detect_langs(text[:1000])[0].prob
        
        print(f"🌍 Language detected: {detected} (confidence: {confidence:.2f})")
        
        # If confidence is too low, try Google Translate detection
        if confidence < 0.8:
            try:
                google_detection = google_translator.detect(text[:500])
                print(f"🌍 Google Translate detection: {google_detection.lang} (confidence: {google_detection.confidence})")
                
                if google_detection.confidence > confidence:
                    return google_detection.lang
            except:
                pass
        
        return detected
        
    except Exception as e:
        print(f"❌ Language detection error: {str(e)}")
        # Fallback: try Google Translate
        try:
            google_detection = google_translator.detect(text[:500])
            return google_detection.lang
        except:
            return 'unknown'

def is_english(text):
    """Check if text is already in English"""
    detected_lang = detect_language(text)
    return detected_lang == 'en'

def translate_with_groq(text, source_lang, target_lang='en', max_chunk_size=2000):
    """
    Translate text using Groq API with proper chunking
    """
    try:
        # If already English, return as is
        if source_lang == 'en' or source_lang == target_lang:
            return text
        
        # Get language names for better prompting
        lang_names = {
            'es': 'Spanish', 'fr': 'French', 'de': 'German', 'it': 'Italian',
            'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese', 'ko': 'Korean',
            'zh': 'Chinese', 'ar': 'Arabic', 'hi': 'Hindi', 'bn': 'Bengali',
            'ur': 'Urdu', 'ta': 'Tamil', 'te': 'Telugu', 'ml': 'Malayalam',
            'kn': 'Kannada', 'gu': 'Gujarati', 'pa': 'Punjabi', 'mr': 'Marathi',
            'ne': 'Nepali', 'si': 'Sinhala', 'my': 'Myanmar', 'th': 'Thai',
            'vi': 'Vietnamese', 'id': 'Indonesian', 'ms': 'Malay', 'tl': 'Filipino'
        }
        
        source_name = lang_names.get(source_lang, f"language code {source_lang}")
        target_name = lang_names.get(target_lang, f"language code {target_lang}")
        
        # Split text into manageable chunks
        chunks = split_text_for_translation(text, max_chunk_size)
        translated_chunks = []
        
        print(f"🌍 Translating {len(chunks)} chunks from {source_name} to {target_name}")
        
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                translated_chunks.append(chunk)
                continue
                
            prompt = f"""You are an expert translator. Translate the following {source_name} text to {target_name}. 

IMPORTANT INSTRUCTIONS:
- Provide ONLY the translation, no explanations or additional text
- Maintain the original formatting and structure
- Preserve technical terms and proper nouns appropriately
- Keep the meaning and tone of the original text
- If you encounter text that's already in {target_name}, keep it as is

Text to translate:
{chunk}

Translation:"""

            try:
                translation = groq_generate(
                    prompt, 
                    max_tokens=min(len(chunk) * 2, 1500),  # Estimate output length
                    temperature=0.1,  # Low temperature for consistent translation
                    timeout=60
                )
                
                if translation:
                    # Clean up the translation (remove any extra explanations)
                    translation = clean_translation_output(translation)
                    translated_chunks.append(translation)
                    print(f"✅ Chunk {i+1}/{len(chunks)} translated successfully")
                else:
                    print(f"⚠️ Groq translation failed for chunk {i+1}, using Google Translate fallback")
                    fallback_translation = translate_with_google(chunk, source_lang, target_lang)
                    translated_chunks.append(fallback_translation)
                    
            except Exception as e:
                print(f"❌ Error translating chunk {i+1}: {str(e)}")
                fallback_translation = translate_with_google(chunk, source_lang, target_lang)
                translated_chunks.append(fallback_translation)
        
        # Join all translated chunks
        full_translation = " ".join(translated_chunks)
        print(f"✅ Translation completed: {len(text)} → {len(full_translation)} characters")
        
        return full_translation
        
    except Exception as e:
        print(f"❌ Groq translation error: {str(e)}")
        return translate_with_google(text, source_lang, target_lang)

def translate_with_google(text, source_lang, target_lang='en'):
    """
    Fallback translation using Google Translate
    """
    try:
        print(f"🌍 Using Google Translate fallback: {source_lang} → {target_lang}")
        
        # Google Translate has a character limit, so we need to chunk
        max_chars = 4500  # Google's limit is ~5000 chars
        chunks = [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
        
        translated_chunks = []
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                translated_chunks.append(chunk)
                continue
                
            try:
                result = google_translator.translate(
                    chunk, 
                    src=source_lang, 
                    dest=target_lang
                )
                translated_chunks.append(result.text)
                print(f"✅ Google Translate chunk {i+1}/{len(chunks)} completed")
                
            except Exception as e:
                print(f"❌ Google Translate error for chunk {i+1}: {str(e)}")
                translated_chunks.append(chunk)  # Keep original if translation fails
        
        return " ".join(translated_chunks)
        
    except Exception as e:
        print(f"❌ Google Translate fallback failed: {str(e)}")
        return text  # Return original text if all translation methods fail

def split_text_for_translation(text, max_size=2000):
    """
    Split text into chunks suitable for translation
    Tries to split at sentence boundaries to maintain context
    """
    if len(text) <= max_size:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Split by paragraphs first
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 2 <= max_size:
            if current_chunk:
                current_chunk += '\n\n' + paragraph
            else:
                current_chunk = paragraph
        else:
            # Save current chunk if it exists
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            
            # If paragraph itself is too long, split by sentences
            if len(paragraph) > max_size:
                sentences = re.split(r'[.!?]\s+', paragraph)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 2 <= max_size:
                        if current_chunk:
                            current_chunk += '. ' + sentence
                        else:
                            current_chunk = sentence
                    else:
                        if current_chunk:
                            chunks.append(current_chunk + '.')
                        current_chunk = sentence
            else:
                current_chunk = paragraph
    
    # Add the last chunk
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def clean_translation_output(translation):
    """
    Clean up translation output to remove any extra text or formatting
    """
    # Remove common prefixes that LLMs might add
    prefixes_to_remove = [
        "Translation:", "Here is the translation:", "The translation is:",
        "Translated text:", "English translation:", "Here's the translation:"
    ]
    
    cleaned = translation.strip()
    
    for prefix in prefixes_to_remove:
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix):].strip()
    
    # Remove quotes if the entire text is wrapped in them
    if (cleaned.startswith('"') and cleaned.endswith('"')) or \
       (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1].strip()
    
    return cleaned

def translate_document_content(raw_text, filename="document"):
    """
    Main function to handle document translation
    Returns: tuple of (translated_text, original_language, was_translated)
    """
    try:
        print(f"🌍 Processing document for translation: {filename}")
        
        # Detect language
        detected_lang = detect_language(raw_text)
        
        if detected_lang == 'unknown':
            print("⚠️ Could not detect language, assuming English")
            return raw_text, 'en', False
        
        if detected_lang == 'en':
            print("✅ Document is already in English")
            return raw_text, 'en', False
        
        print(f"🌍 Document language: {detected_lang}, translating to English...")
        
        # Translate to English
        translated_text = translate_with_groq(raw_text, detected_lang, 'en')
        
        if not translated_text or translated_text == raw_text:
            print("⚠️ Translation may have failed, using original text")
            return raw_text, detected_lang, False
        
        print(f"✅ Translation completed successfully")
        return translated_text, detected_lang, True
        
    except Exception as e:
        print(f"❌ Translation process error: {str(e)}")
        return raw_text, 'unknown', False

def translate_query(query, target_lang='en'):
    """
    Translate user queries if needed
    """
    try:
        detected_lang = detect_language(query)
        
        if detected_lang == target_lang:
            return query, detected_lang
        
        print(f"🌍 Translating query from {detected_lang} to {target_lang}")
        translated_query = translate_with_groq(query, detected_lang, target_lang)
        
        return translated_query, detected_lang
        
    except Exception as e:
        print(f"❌ Query translation error: {str(e)}")
        return query, 'unknown'