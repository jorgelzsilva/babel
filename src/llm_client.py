from openai import OpenAI
import time
from . import config

class LLMClient:
    def __init__(self, base_url=None, api_key=None):
        self.client = OpenAI(
            base_url=base_url or config.LM_STUDIO_URL,
            api_key=api_key or config.API_KEY
        )
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0

    def translate_chunk(self, text_chunk, system_prompt):
        """
        Sends a chunk of text to the LLM for translation.
        
        Args:
            text_chunk (list): A list of strings (paragraphs) to translate.
            system_prompt (str): The system instructions for translation.
            
        Returns:
            list: The translated paragraphs.
        """
        if not text_chunk:
            return []

        # Join paragraphs with a delimiter to keep context but separate them easily later?
        # A safer approach for list-to-list translation is forcing the LLM to return JSON or a specific format.
        # But for prose, context is key.
        # Strategy: Join with newlines, ask LLM to maintain paragraph structure.
        
        # Strategy: Use numbered list to enforce count and order.
        # e.g. 
        # 1. Text A
        # 2. Text B
        
        numbered_input = "\n".join([f"[{i+1}] {text}" for i, text in enumerate(text_chunk)])
        
        # We need to inform the LLM about the format in the prompt
        format_instruction = f"Translate the following {len(text_chunk)} items. Return exactly {len(text_chunk)} items, numbered like [1], [2], etc. One per line. Do not merge chunks."

        messages = [
            {"role": "system", "content": system_prompt + "\n" + format_instruction},
            {"role": "user", "content": numbered_input}
        ]

        last_result = []

        for attempt in range(config.MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model="local-model", 
                    messages=messages,
                    temperature=0.3, 
                )
                
                translated_text = response.choices[0].message.content.strip()
                
                # Track usage
                if response.usage:
                    self.total_prompt_tokens += response.usage.prompt_tokens
                    self.total_completion_tokens += response.usage.completion_tokens
                    self.total_tokens += response.usage.total_tokens
                
                # Parse the numbered list back
                import re
                # Regex to match [N] ... or N. ... 
                # dealing with potential newlines inside the text is tricky if we just split by line.
                # But if we asked for "One per line", for paragraphs it might break internal newlines.
                # Let's try splitting by the marker `[\d+]`
                
                # Robust parsing:
                # We expect markers like [1], [2], ...
                # We can split by regex `\[\d+\]`
                
                parts = re.split(r'\[\d+\]', translated_text)
                # First part is usually empty (before [1])
                clean_parts = [p.strip() for p in parts if p.strip()]
                
                # Validation
                if len(clean_parts) == len(text_chunk):
                    return clean_parts
                
                print(f"Translation mismatch (Attempt {attempt+1}/{config.MAX_RETRIES}): Sent {len(text_chunk)}, got {len(clean_parts)}. Retrying...")
                last_result = clean_parts

            except Exception as e:
                print(f"Error during translation request (Attempt {attempt+1}): {e}")
                if attempt == config.MAX_RETRIES - 1:
                    raise e
                time.sleep(1) # Backoff
                
        return last_result # Return best effort, Translator handles fallback
