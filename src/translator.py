from .llm_client import LLMClient
from . import config, utils
import math

class Translator:
    def __init__(self, llm_client: LLMClient, prompt_file=None):
        self.llm_client = llm_client
        self.system_prompt = utils.load_prompt(prompt_file or config.DEFAULT_PROMPT_FILE)

    def process_file(self, handler, output_path):
        """
        Orchestrates the translation of a file.
        """
        print(f"Reading file: {handler.file_path}")
        handler.read_file()
        
        print("Extracting text...")
        text_nodes = handler.extract_text()
        
        # text_nodes is a list of objects/dicts, we assume they have a 'text' attribute or key
        # For simplicity, let's assume the handler returns a list of objects where obj.text is the string
        # If the handler returns a list of strings directly, we can't update them in place easily without an index map.
        # So we expect objects.
        
        original_texts = [node.text for node in text_nodes if node.text and node.text.strip()]
        
        if not original_texts:
            print("No text found to translate.")
            handler.save_file(output_path)
            return

        print(f"Found {len(original_texts)} text segments. Starting translation...")
        
        chunks = self._create_chunks(original_texts)
        translated_segments = []
        
        total_chunks = len(chunks)
        for i, chunk in enumerate(chunks):
            print(f"Translating chunk {i+1}/{total_chunks} ({len(chunk)} items)...")
            
            # Try to translate robustly
            translated_chunk = self._translate_recursive(chunk)
            translated_segments.extend(translated_chunk)



        # We need to map back the translated texts to the original nodes.
        # We only translated non-empty texts. We must correspond them correctly.
        
        # Create a full list of translations matching the original text_nodes (including empty/skipped ones if any)
        # Actually, we filtered by `if node.text and node.text.strip()`.
        # So `translated_segments` only corresponds to those.
        
        # We need a way to pass exactly the translated valid segments back to the handler
        # OR the handler takes the full list and we only update the valid ones.
        
        # Let's rebuild a map or just pass the list of 'valid' translations
        # and let the handler apply them effectively.
        # But wait, `extract_text` returned ALL nodes or just valid ones? 
        # Better if `extract_text` returns ALL, and we filter here.
        # The logic `original_texts = [node.text ...]` creates a subset.
        # We need to apply back to those specific nodes.
        
        # Let's iterate and apply directly here? No, Handler should do it to keep encapsulation?
        # Actually, simpler:
        # We have `text_nodes` (subset of valid nodes ideally? or all?).
        # Let's assume `text_nodes` are VALID nodes we want to translate.
        # If the handler returned everything, we should have filtered `text_nodes` list itself.
        
        valid_nodes = [node for node in text_nodes if node.text and node.text.strip()]
        
        if len(valid_nodes) != len(translated_segments):
            print("CRITICAL ERROR: Translation count mismatch with valid nodes.")
            # Fallback
            return

        # Apply translations
        for node, trans_text in zip(valid_nodes, translated_segments):
            node.text = trans_text
            
        print("Saving file...")
        handler.save_file(output_path)
        print(f"Saved to {output_path}")

    def _create_chunks(self, texts):
        """
        Groups texts into chunks based on constraints (3 paragraphs or 8192 tokens).
        """
        chunks = []
        current_chunk = []
        current_token_count = 0
        
        for text in texts:
            # Estimate tokens (rough estimate: 1 token ~= 4 chars)
            # OpenAI rule of thumb: 1 token ~= 4 chars in English. 
            # For robustness, we check length.
            tokens = len(text) // 4
            
            # Check conditions
            # 1. Paragraph count limit (3)
            # 2. Token limit (8192)
            
            # If adding this would exceed limits, yield current and start new
            if (len(current_chunk) >= config.MAX_PARAGRAPHS) or \
               (current_token_count + tokens > config.MAX_TOKENS):
                chunks.append(current_chunk)
                current_chunk = []
                current_token_count = 0
            
            current_chunk.append(text)
            current_token_count += tokens
            
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks

    def _translate_recursive(self, chunk):
        """
        Tries to translate a chunk. If it fails (length mismatch), splits it in half and tries recursively.
        """
        # Base case: empty
        if not chunk:
            return []

        # Try translating the whole chunk
        try:
            translated = self.llm_client.translate_chunk(chunk, self.system_prompt)
            if len(translated) == len(chunk):
                return translated
        except Exception as e:
            print(f"Error translating chunk of size {len(chunk)}: {e}")

        # If we are here, we failed to get a perfect match.
        
        # Base case: single item failed even after retries
        if len(chunk) == 1:
            print(f"WARNING: Failed to translate single item. Keeping original.")
            return chunk # Return original as fallback

        # Recursive Step: Split in half
        mid = len(chunk) // 2
        print(f"Splitting failing chunk of size {len(chunk)} into {mid} and {len(chunk)-mid}...")
        
        left_chunk = chunk[:mid]
        right_chunk = chunk[mid:]
        
        return self._translate_recursive(left_chunk) + self._translate_recursive(right_chunk)
