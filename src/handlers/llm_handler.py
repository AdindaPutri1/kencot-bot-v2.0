"""
LLM Handler untuk Groq API
"""
import os
from openai import OpenAI
from src.config import Config
import logging

logger = logging.getLogger(__name__)

# Initialize Groq client
groq_client = None
if Config.GROQ_API_KEY:
    try:
        groq_client = OpenAI(
            api_key=Config.GROQ_API_KEY,
            base_url=getattr(Config, 'LLM_BASE_URL', 'https://api.groq.com/openai/v1')
        )
        logger.info("[OK] Groq client initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Groq client: {e}")

# Initialize Gemini client if needed
gemini_client = None
if Config.GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=Config.GEMINI_API_KEY)
        gemini_client = genai.GenerativeModel(Config.GEMINI_MODEL_NAME)
        logger.info("✓ Gemini client initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Gemini client: {e}")

def ask_gemini(prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
    """
    Send prompt to Gemini API
    """
    try:
        if gemini_client:
            response = gemini_client.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                }
            )
            return response.text
        elif groq_client:
            # Fallback to Groq if Gemini not available
            logger.info("Gemini not available, using Groq instead")
            return ask_groq(prompt, max_tokens, temperature)
        else:
            logger.error("No LLM client available")
            return "Maaf, sistem lagi gangguan. Coba lagi nanti ya!"
    except Exception as e:
        logger.error(f"Error calling Gemini: {e}")
        # Fallback to Groq
        if groq_client:
            return ask_groq(prompt, max_tokens, temperature)
        return "Maaf, ada error saat memproses permintaan kamu."

def ask_groq(prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
    """
    Send prompt to Groq API
    """
    try:
        if not groq_client:
            logger.error("Groq client not initialized")
            return "Maaf, sistem belum siap. Pastikan GROQ_API_KEY sudah diset."
        
        response = groq_client.chat.completions.create(
            model=Config.GROQ_MODEL_NAME,
            messages=[
                {"role": "system", "content": "Kamu adalah asisten yang membantu mencari makanan di UGM."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        logger.error(f"Error calling Groq: {e}", exc_info=True)
        return "Maaf, ada error saat memproses permintaan kamu."

def get_llm_response(prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
    """
    Get LLM response using configured provider
    """
    llm_model = getattr(Config, 'LLM_MODEL', 'groq').lower()
    
    if llm_model == 'gemini' and gemini_client:
        return ask_gemini(prompt, max_tokens, temperature)
    elif llm_model == 'groq' and groq_client:
        return ask_groq(prompt, max_tokens, temperature)
    else:
        # Auto-fallback
        if groq_client:
            return ask_groq(prompt, max_tokens, temperature)
        elif gemini_client:
            return ask_gemini(prompt, max_tokens, temperature)
        else:
            logger.error("No LLM provider available")
            return "Maaf, sistem belum dikonfigurasi dengan benar."

def extract_json_from_response(response: str) -> dict:
    """
    Extract JSON from LLM response that might contain markdown code blocks
    """
    import json
    import re
    
    # Try to find JSON in markdown code blocks
    json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    match = re.search(json_pattern, response, re.DOTALL)
    
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
    
    # Try to parse entire response as JSON
    try:
        return json.loads(response)
    except:
        pass
    
    # Try to find JSON object in response
    json_obj_pattern = r'\{[^{}]*\}'
    match = re.search(json_obj_pattern, response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            pass
    
    return {}