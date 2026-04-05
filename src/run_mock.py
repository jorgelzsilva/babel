from src.translator import Translator
from src.main import get_handler
from src.llm_client import LLMClient
import os

# Mock LLM Client
class MockLLMClient:
    def translate_chunk(self, text_chunk, prompt):
        return [f"[PT] {text}" for text in text_chunk]

def run_test():
    print("Running Mock Test...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_root = os.path.dirname(script_dir)
    input_dir = os.path.join(base_root, 'input')
    output_dir = os.path.join(base_root, 'output')
    
    files = ["sample.cxml", "sample.docx", "sample.epub"]
    
    client = MockLLMClient()
    translator = Translator(client)
    
    for f in files:
        in_path = os.path.join(input_dir, f)
        out_path = os.path.join(output_dir, f)
        
        if not os.path.exists(in_path):
            print(f"File missing: {in_path}")
            continue
            
        print(f"Testing {f}...")
        handler = get_handler(in_path)
        translator.process_file(handler, out_path)
        
        if os.path.exists(out_path):
            print(f"SUCCESS: {out_path} created.")
        else:
            print(f"FAILURE: {out_path} not found.")

if __name__ == "__main__":
    run_test()
