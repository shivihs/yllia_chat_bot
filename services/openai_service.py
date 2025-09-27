import os
from openai import OpenAI
from dotenv import load_dotenv
from config.constants import OPENAI_MODEL
from services.prompt_sevice import load_prompt

# Load environment variables
load_dotenv()

# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set in environment variables")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

def ask_openai(user_input: str, ctx_static: str = "", ctx_dynamic: str = "", speech_history: str = "") -> str:
    """
    Funkcja wysyła pytanie użytkownika do OpenAI z pełnym promptem.
    """
    system_prompt = load_prompt(ctx_static, ctx_dynamic, speech_history)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        temperature=0.3,
    )

    # Zwraca odpowiedź OpenAI, zamieniając każde "siwicki.info" na link
    content = response.choices[0].message.content
    # Zamiana "siwicki.info" na link do https://siwicki.info
    content = content.replace("siwicki.info", "[siwicki.info](https://siwicki.info)")
    return content

# Proste zapytanie do OpenAI
def ask_openai_simple(user_prompt: str) -> str:
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": user_prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content

