from services.openai_service import ask_openai_simple
from config.config import PROMPT_SUMMARY, PROMPT_PATIENTS_SUMMARY
from config.constants import OPENAI_MODEL
import tiktoken

def format_history(messages: list[dict]) -> str:
    """
    Proste formatowanie historii: role + treść
    """
    formatted = []
    for msg in messages:
        role = "Pacjent" if msg["role"] == "user" else "Yllia"
        formatted.append(f"{role}: {msg['content']}")
    return "\n".join(formatted)

def summarize_full_history(messages: list[dict]) -> tuple[str, int]:
    """
    Używa OpenAI do streszczenia całej historii rozmowy.
    Zwraca tuple: (odpowiedź, liczba tokenów wejściowych).
    """
    try:
        if not messages:
            return "", 0

        text = format_history(messages)
        with open(PROMPT_SUMMARY, "r", encoding="utf-8") as f:
            prompt_template = f.read()
        prompt = prompt_template.replace("conversation", text)

        # Liczenie tokenów wejściowych
        try:
            encoding = tiktoken.encoding_for_model(OPENAI_MODEL)
            token_input_count = len(encoding.encode(prompt))
        except Exception as e:
            print(f"Błąd przy liczeniu tokenów: {str(e)}")
            token_input_count = 0

        try:
            response = ask_openai_simple(prompt)
            return response, token_input_count
        except Exception as e:
            print(f"Błąd przy wywołaniu OpenAI w summarize_full_history: {str(e)}")
            return "Nie udało się wygenerować podsumowania rozmowy.", token_input_count

    except Exception as e:
        print(f"Błąd w summarize_full_history: {str(e)}")
        return "Wystąpił błąd podczas przetwarzania historii rozmowy.", 0

def summarize_full_history_for_patients(messages: list[dict], speech_history: str) -> tuple[str, int]:
    """
    Używa OpenAI do streszczenia całej historii rozmowy.
    Zwraca tuple: (odpowiedź, liczba tokenów wejściowych).
    """
    try:
        if not messages:
            return "", 0

        text = format_history(messages)
        with open(PROMPT_PATIENTS_SUMMARY, "r", encoding="utf-8") as f:
            prompt_template = f.read()
        prompt = prompt_template.replace("conversation", text).replace("conversation_summary", speech_history)

        # Liczenie tokenów wejściowych
        try:
            encoding = tiktoken.encoding_for_model(OPENAI_MODEL)  # lub inny model, jeśli używasz innego
            token_input_count = len(encoding.encode(prompt))
        except Exception as e:
            print(f"Błąd przy liczeniu tokenów: {str(e)}")
            token_input_count = 0

        try:
            response = ask_openai_simple(prompt)
            return response, token_input_count
        except Exception as e:
            print(f"Błąd przy wywołaniu OpenAI w summarize_full_history_for_patients: {str(e)}")
            return "Nie udało się wygenerować podsumowania rozmowy.", token_input_count

    except Exception as e:
        print(f"Błąd w summarize_full_history_for_patients: {str(e)}")
        return "Wystąpił błąd podczas przetwarzania historii rozmowy.", 0