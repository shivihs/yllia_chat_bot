import os

PROMPT_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")

def load_prompt(filename: str, **kwargs) -> str:
    """
    Ładuje prompt z pliku i podstawia zmienne z kwargs.
    Przykład:
      load_prompt("prompt_general.md", ctx_static="...", ctx_dynamic="...", user_input="...")
    """
    filepath = os.path.join(PROMPT_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    # zamiana {placeholders} na wartości
    return text.format(**kwargs)
