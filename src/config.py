import os

# LM Studio Configuration
LM_STUDIO_URL = "http://localhost:1234/v1"
API_KEY = "lm-studio" # Local server doesn't usually need a real key

# Chunking Configuration
MAX_PARAGRAPHS = 20
MAX_TOKENS = 8192

# Retry/Timeout Configuration
REQUEST_TIMEOUT = 300 # seconds (5 minutes for slow local inference)
MAX_RETRIES = 3

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS_DIR = os.path.join(BASE_DIR, 'prompts')
DEFAULT_PROMPT_FILE = os.path.join(PROMPTS_DIR, 'translation_prompt.txt')
