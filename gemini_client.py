import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure API Key
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def generate_answer(query: str, context_chunks: list[str]) -> str:
    """
    Generates an answer based strictly on the provided context using Gemini.
    """
    if not api_key:
        return "Error: GEMINI_API_KEY environment variable not set."

    if not context_chunks:
        return "I don't have information on that in the provided document."

    context_text = "\n\n".join([f"--- Chunk ---\n{chunk}" for chunk in context_chunks])
    
    system_instruction = (
        "You are a helpful AI assistant. Your task is to answer the user's question "
        "using ONLY the provided context. If the answer cannot be found in the context, "
        "you MUST reply exactly with: 'I don't have information on that in the provided document.' "
        "Do not use any outside knowledge.\n"
        "IMPORTANT: Do not start your answer with repetitive phrases like 'Based on the provided document' or 'According to the context'. Just answer the question directly and naturally.\n\n"
    )
    
    prompt = f"{system_instruction}Context information:\n{context_text}\n\nUser Question:\n{query}"
    
    try:
        # Using gemini-3.5-flash as it is supported in 2026.
        model = genai.GenerativeModel('gemini-3.5-flash')
        
        # Use a low temperature to ensure grounded output
        generation_config = genai.types.GenerationConfig(
            temperature=0.1
        )
        
        response = model.generate_content(prompt, generation_config=generation_config)
        return response.text
    except Exception as e:
        return f"An error occurred while generating the response: {str(e)}"
