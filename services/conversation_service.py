from services.openai_service import ask_openai_simple
from config.config import PROMPT_SUMMARY, PROMPT_PATIENTS_SUMMARY, PROMPT_TRANSLATE_TO_POLISH, PROMPT_TRANSLATE_FROM_POLISH
from config.constants import OPENAI_MODEL, MAX_INPUT, SUPPORTED_LANGUAGES
import tiktoken
from collections import Counter
from typing import Optional
import json

ENCODER = tiktoken.encoding_for_model(OPENAI_MODEL)

class LanguageTracker:
    """
    Klasa do śledzenia języków używanych w sesji i określania dominującego języka.
    """
    
    def __init__(self):
        self._languages: list[str] = []
    
    def add_language(self, language_code: str) -> None:
        """
        Dodaje wykryty język do historii.
        
        Args:
            language_code: kod języka (np. 'pl', 'en', 'de')
        """
        if language_code and language_code != "unknown":
            self._languages.append(language_code)
    
    def get_dominant_language(self) -> str:
        """
        Zwraca najczęściej używany język w sesji.
        Domyślnie zwraca 'pl' jeśli brak danych.
        
        Returns:
            kod najczęstszego języka
        """
        if not self._languages:
            return 'pl'
        
        counter = Counter(self._languages)
        return counter.most_common(1)[0][0]
    
    def last_added(self) -> Optional[str]:
        """
        Zwraca ostatnio dodany język.
        
        Returns:
            kod ostatniego języka lub None jeśli lista pusta
        """
        return self._languages[-1] if self._languages else None
    
    def get_language_stats(self) -> dict[str, int]:
        """
        Zwraca statystyki użycia języków.
        
        Returns:
            słownik z kodami języków i liczbą wystąpień
        """
        return dict(Counter(self._languages))
    
    def get_all_languages(self) -> list[str]:
        """
        Zwraca listę wszystkich wykrytych języków (z duplikatami).
        
        Returns:
            lista kodów języków w kolejności wykrycia
        """
        return self._languages.copy()
    
    def clear(self) -> None:
        """Czyści historię języków."""
        self._languages.clear()
    
    def __len__(self) -> int:
        """Zwraca liczbę zapisanych wykryć języka."""
        return len(self._languages)
    
    def __repr__(self) -> str:
        stats = self.get_language_stats()
        last = self.last_added()
        return f"LanguageTracker(dominant='{self.get_dominant_language()}', last='{last}', stats={stats})"



def detect_and_translate_to_polish(text: str) -> tuple[str, str, int]:
    """
    Wykrywa język tekstu i tłumaczy na polski jeśli potrzeba.
    
    Args:
        text: tekst do analizy
        
    Returns:
        tuple: (przetłumaczony_tekst, wykryty_język, liczba_tokenów)
    """
    with open(PROMPT_TRANSLATE_TO_POLISH, "r", encoding="utf-8") as f:
        prompt_template = f.read()
    prompt = prompt_template.replace("{text}", text)

    # Liczenie tokenów wejściowych
    token_count = len(ENCODER.encode(prompt))
    
    try:
        response = ask_openai_simple(prompt)
        
        # Dodaj tokeny wyjściowe
        token_count += len(ENCODER.encode(prompt + response))
        
        result = json.loads(response)
        
        return (
            result.get("translated_text", text),
            result.get("language", "unknown"),
            token_count
        )
        
    except Exception as e:
        print(f"Błąd w detect_and_translate_to_polish: {str(e)}")
        return text, "unknown", token_count


def translate_from_polish(text: str, target_language: str) -> tuple[str, int]:
    """
    Tłumaczy tekst z polskiego na zadany język.
    
    Args:
        text: tekst po polsku do przetłumaczenia
        target_language: kod języka docelowego (np. 'en', 'de', 'es')
        
    Returns:
        tuple: (przetłumaczony_tekst, liczba_tokenów)
    """
   
    target_lang_name = SUPPORTED_LANGUAGES.get(target_language, target_language)
    
    with open(PROMPT_TRANSLATE_FROM_POLISH, "r", encoding="utf-8") as f:
        prompt_template = f.read()
    prompt = prompt_template.replace("{text}", text).replace("{target_lang_name}", target_lang_name)

    # Liczenie tokenów wejściowych
    token_count = len(ENCODER.encode(prompt))
    
    try:
        response = ask_openai_simple(prompt)
        
        translated = response
        
        # Dodaj tokeny wyjściowe
        token_count += len(ENCODER.encode(prompt + translated))
        
        return translated, token_count
        
    except Exception as e:
        print(f"Błąd w translate_from_polish: {str(e)}")
        return text, token_count

def format_history(messages: list[dict]) -> str:
    """
    Proste formatowanie historii: role + treść
    """
    formatted = []
    for msg in messages:
        role = "Pacjent" if msg["role"] == "user" else "Yllia"
        formatted.append(f"{role}: {msg['content']}")
    return "\n".join(formatted)

def check_length(text: str) -> bool:
    """
    Sprawdza długość tekstu.
    """
    if len(text) > MAX_INPUT:
        return False # Za długi tekst
    else:
        return True # Poprawna długość

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
