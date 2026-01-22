import os
import sys
import time
from . import config
from .llm_client import LLMClient
from .translator import Translator
from .format_handlers.cxml_handler import CXMLHandler
from .format_handlers.docx_handler import DocxHandler
from .format_handlers.epub_handler import EpubHandler

def get_handler(file_path):
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext in ['.xml', '.cxml']:
        return CXMLHandler(file_path)
    elif ext in ['.docx']:
        return DocxHandler(file_path)
    elif ext in ['.epub']:
        return EpubHandler(file_path)
    else:
        return None

def main():
    start_time = time.perf_counter()
    print("Project Babel - AI Translator Initialized")
    
    # Ensure directories exist
    input_dir = os.path.join(config.BASE_DIR, 'input')
    output_dir = os.path.join(config.BASE_DIR, 'output')
    
    if not os.path.exists(input_dir):
        print(f"Input directory not found: {input_dir}")
        return
        
    files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
    
    if not files:
        print("No files found in input directory.")
        return
        
    # Initialize Core
    try:
        client = LLMClient()
        translator = Translator(client)
    except Exception as e:
        print(f"Failed to initialize AI Client: {e}")
        return

    print(f"Found {len(files)} files to process.")
    
    for filename in files:
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        
        print(f"\n--- Processing: {filename} ---")
        
        handler = get_handler(input_path)
        if not handler:
            print(f"Skipping unsupported file type: {filename}")
            continue
            
        try:
            translator.process_file(handler, output_path)
            print("Done.")
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            import traceback
            traceback.print_exc()

    end_time = time.perf_counter()
    duration = end_time - start_time
    
    print("\n" + "="*50)
    print("PROCESS SUMMARY")
    print("="*50)
    print(f"Total Time: {duration:.2f} seconds")
    
    if 'client' in locals() and hasattr(client, 'total_tokens'):
        tokens = client.total_tokens
        prompt_tokens = client.total_prompt_tokens
        completion_tokens = client.total_completion_tokens
        
        tps = tokens / duration if duration > 0 else 0
        
        print(f"Prompt Tokens:     {prompt_tokens}")
        print(f"Completion Tokens: {completion_tokens}")
        print(f"Total Tokens:      {tokens}")
        print(f"Tokens/Second:     {tps:.2f} t/s")
    print("="*50)

if __name__ == "__main__":
    main()
