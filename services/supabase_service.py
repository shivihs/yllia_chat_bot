from supabase import create_client
from config.config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime
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
    return supabase.table("yllia_sessions").insert({
        "session_id": session_id,
        # "started_at": datetime.now()
    }).execute()

def sessions_end(session_id: str):   
    """
    Zamyka sesję w Supabase.
    """
    return supabase.table("yllia_sessions").update({
        "ended_at": datetime.now(),
    }).eq("session_id", session_id).execute()

def sessions_update(session_id: str, score_final: int, score_note: str = "", chat_summary: str = ""):
    """
    Aktualizuje sesję w Supabase.
    """
    return supabase.table("yllia_sessions").update({
        "score_final": score_final,
        "score_note": score_note,
        "chat_summary": chat_summary
    }).eq("session_id", session_id).execute()
    
def sessions_get(session_id: str):
    """
    Pobiera sesję z Supabase.
    """
    return supabase.table("yllia_sessions").select("*").eq("session_id", session_id).execute()

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
# usage jsonb string
#

def messages_new(session_id: int, user_input: str, context_static: str, context_dynamic: str, context_history: str = "", model: str = "", usage: str = ""):
    """
    Tworzy nową wiadomość w Supabase.
    """
    return supabase.table("yllia_messages").insert({
        "session_id": session_id,
        "user_input": user_input,
        "context_static": context_static,
        "context_dynamic": context_dynamic,
        "context_history": context_history,
        "model": model,
        "usage": usage
    }).execute()

def messages_score(message_id: int, score_up_down: bool):
    """
    Aktualizuje ocenę wiadomości w Supabase.
    """
    return supabase.table("yllia_messages").update({
        "score_up_down": score_up_down
    }).eq("id", message_id).execute()

def messages_get(message_id: int):
    """
    Pobiera wiadomość z Supabase.
    """
    return supabase.table("yllia_messages").select("*").eq("id", message_id).execute()

def messages_get_by_session_id(session_id: int):
    """
    Pobiera wiadomości z Supabase po id sesji.
    """
    return supabase.table("yllia_messages").select("*").eq("session_id", session_id).execute()  

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
    return supabase.table("yllia_prompts").insert({
        "session_id": session_id,
        "prompt_name": prompt_name,
        "prompt": prompt
    }).execute()

def prompts_get(prompt_name: str):
    """
    Pobiera prompt z Supabase.
    """
    return supabase.table("yllia_prompts").select("*").eq("prompt_name", prompt_name).execute()

def prompts_get_all():
    """
    Pobiera wszystkie prompty z Supabase.
    """
    return supabase.table("yllia_prompts").select("*").execute()