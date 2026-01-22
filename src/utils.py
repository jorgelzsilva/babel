import os

def load_prompt(file_path):
    """
    Loads the generic system prompt from a text file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Prompt file not found at: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read().strip()
