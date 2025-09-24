from config.config import PROMPT_GENERAL, PROMPT_SUMMARY, PROMPT_PATIENTS_SUMMARY
import services.supabase_service as supabase_service

def load_prompt_from_file(PROMPT_NAME: str) -> str:
    """
    Ładuje prompt z pliku.
    """
    with open(PROMPT_NAME, "r", encoding="utf-8") as f:
        return f.read()

def save_prompts_to_database(session_id: str):
    """
    Zapisuje prompty do bazy danych.
    """
    supabase_service.prompts_add(session_id, "PROMPT_GENERAL", load_prompt_from_file(PROMPT_GENERAL))
    supabase_service.prompts_add(session_id, "PROMPT_SUMMARY", load_prompt_from_file(PROMPT_SUMMARY))
    supabase_service.prompts_add(session_id, "PROMPT_PATIENTS_SUMMARY", load_prompt_from_file(PROMPT_PATIENTS_SUMMARY))

def load_prompt(PROMPT_NAME: str, **kwargs) -> str:
    """
    Ładuje prompt i podstawia zmienne z kwargs.
    Przykład:
      load_prompt(PROMPT_GENERAL, ctx_static="...", ctx_dynamic="...", conversation="...")
    """
    return PROMPT_NAME.format(**kwargs)

def load_prompt(ctx_static: str, ctx_dynamic: str, conversation_summarized: str) -> str:
    """
    Ładuje i składa główny prompt z kontekstami.
    """

    prompt_template = load_prompt_from_file(PROMPT_GENERAL)
    
    # podmiana znaczników
    system_prompt = prompt_template.replace("ctx_static", ctx_static).replace("ctx_dynamic", ctx_dynamic).replace("conversation_summarized", conversation_summarized)
    return system_prompt