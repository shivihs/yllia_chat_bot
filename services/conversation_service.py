from services.openai_service import ask_openai_simple
from config.config import PROMPT_SUMMARY


def format_history(messages: list[dict]) -> str:
    """
    Proste formatowanie historii: role + treść
    """
    formatted = []
    for msg in messages:
        role = "Pacjent" if msg["role"] == "user" else "Yllia"
        formatted.append(f"{role}: {msg['content']}")
    return "\n".join(formatted)

def summarize_full_history(messages: list[dict]) -> str:
    """
    Używa OpenAI do streszczenia całej historii rozmowy.
    """
    try:
        if not messages:
            return ""
            
        text = format_history(messages)
        with open(PROMPT_SUMMARY, "r", encoding="utf-8") as f:
            prompt_template = f.read()
        prompt = prompt_template.replace("conversation", text)
        
        try:
            return ask_openai_simple(prompt)
        except Exception as e:
            print(f"Błąd przy wywołaniu OpenAI w summarize_full_history: {str(e)}")
            return "Nie udało się wygenerować podsumowania rozmowy."
            
    except Exception as e:
        print(f"Błąd w summarize_full_history: {str(e)}")
        return "Wystąpił błąd podczas przetwarzania historii rozmowy."