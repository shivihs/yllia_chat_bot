from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_TABLE_SESSIONS, SUPABASE_TABLE_MESSAGES, SUPABASE_TABLE_PROMPTS
from datetime import datetime, timezone
import os

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

#
# Obsługa tabeli: yllia_sessions
#
# id bigint number	
# session_id uuid string
# started_at timestamp with time zone string 
# ended_at timestamp with time zone string
# score_final smallint number
# score_note text string
# chat_summary text string
#

def sessions_new(session_id: str):
    """
    Tworzy nową sesję w Supabase.
    """
    return supabase.table(SUPABASE_TABLE_SESSIONS).insert({
        "session_id": session_id,
    }).execute()

def sessions_end(session_id: str):   
    """
    Zamyka sesję w Supabase.
    """
    return supabase.table(SUPABASE_TABLE_SESSIONS).update({
        "ended_at": datetime.now(timezone.utc).isoformat(),
    }).eq("session_id", session_id).execute()

def sessions_update(session_id: str, score_final: int = None, score_note: str = "", usage_total: int = 0, chat_summary: str = ""):
    """
    Aktualizuje sesję w Supabase.
    """
    return supabase.table(SUPABASE_TABLE_SESSIONS).update({
        "score_final": score_final,
        "score_note": score_note,
        "usage_total": usage_total,
        "chat_summary": chat_summary
    }).eq("session_id", session_id).execute()
    
def sessions_get(session_id: str):
    """
    Pobiera sesję z Supabase.
    """
    return supabase.table(SUPABASE_TABLE_SESSIONS).select("*").eq("session_id", session_id).execute()

#
# Obsługa tabeli: yllia_messages
#
# id bigint number
# created_at timestamp with time zone string
# session_id uuid string
# user_input text string
# context_static jsonb string
# context_dynamic jsonb string
# context_history text string
# score_up_down boolean boolean
# model text string
# usage_input smallint number
# usage_output smallint number
# chat_output text string
#


def messages_add(session_id: str, user_input: str, context_static: str, context_dynamic: str, context_history: str = "", model: str = "", usage_input: int = 0, usage_output: int = 0, chat_output: str = "", language: str = ""):
    """
    Tworzy nową wiadomość w Supabase.
    
    Args:
        session_id: UUID sesji w formie stringa
        user_input: pytanie użytkownika
        context_static: kontekst statyczny (baza wiedzy)
        context_dynamic: kontekst dynamiczny (dane administracyjne)
        context_history: historia rozmowy
        model: nazwa modelu
        usage_input: liczba tokenów wejściowych
        usage_output: liczba tokenów wyjściowych
        chat_output: odpowiedź asystenta
        language: język wiadomości
    """
    result = supabase.table(SUPABASE_TABLE_MESSAGES).insert({
        "session_id": session_id,
        "user_input": user_input,
        "context_static": context_static,
        "context_dynamic": context_dynamic,
        "context_history": context_history,
        "model": model,
        "usage_input": usage_input,
        "usage_output": usage_output,
        "chat_output": chat_output,
        "language": language
    }).execute()
    return result


def messages_update_score(session_id: str, score_up_down: bool):
    """
    Aktualizuje feedback (👍/👎) dla ostatniej wiadomości w sesji.
    
    Args:
        session_id: UUID sesji w formie stringa
        score_up_down: True dla 👍, False dla 👎
    """
    try:
        # Upewnij się że session_id jest stringiem
        session_id_str = str(session_id)

        # Pobierz ID ostatniej wiadomości
        last_message = supabase.table(SUPABASE_TABLE_MESSAGES)\
            .select("id, session_id, created_at")\
            .eq("session_id", session_id_str)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()

        if not last_message.data:
            return
        
        message_id = last_message.data[0]["id"]
        created_at = last_message.data[0]["created_at"]
        
        # Zaktualizuj feedback
        update_result = supabase.table(SUPABASE_TABLE_MESSAGES)\
            .update({"score_up_down": score_up_down})\
            .eq("id", message_id)\
            .execute()
        
    except Exception as e:
        print(f"[ERROR] Failed to update message score: {str(e)}")
        raise  # Re-raise exception to handle it in the calling code
    

#
# Obsługa tabeli: yllia_prompts
#
# id bigint number
# created_at timestamp with time zone string
# prompt_name text string
# prompt text string
#

def prompts_add(session_id: str, prompt_name: str, prompt: str):
    """
    Tworzy nowy prompt w Supabase.
    """
    return supabase.table(SUPABASE_TABLE_PROMPTS).insert({
        "session_id": session_id,
        "prompt_name": prompt_name,
        "prompt": prompt
    }).execute()

def prompts_get(prompt_name: str):
    """
    Pobiera prompt z Supabase.
    """
    return supabase.table(SUPABASE_TABLE_PROMPTS).select("*").eq("prompt_name", prompt_name).execute()

def prompts_get_all():
    """
    Pobiera wszystkie prompty z Supabase.
    """
    return supabase.table(SUPABASE_TABLE_PROMPTS).select("*").execute()