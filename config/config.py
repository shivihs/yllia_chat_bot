import os
from dotenv import load_dotenv

load_dotenv()  # wczytuje klucze z .env

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Langfuse
LANGFUSE_API_KEY = os.getenv("LANGFUSE_API_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")

# Qdrant
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)  # jeśli nie ma autoryzacji, zostaw None

# Prompts
PROMPT_GENERAL = os.path.join(os.path.dirname(__file__), "..", "prompts", "prompt_general.md") # Prompt z jakiego korzystamy w aplikacji
PROMPT_SUMMARY = os.path.join(os.path.dirname(__file__), "..", "prompts", "prompt_summary.md") # Prompt do streszczenia historii rozmowy

# Limity
MAX_HISTORY_MESSAGES = 5
