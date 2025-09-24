from langfuse import get_client
from dotenv import load_dotenv
from typing import Optional
from config.config import LANGFUSE_ENABLED, LANGFUSE_API_KEY, LANGFUSE_HOST

load_dotenv()

#
# Inicjalizacja klienta Langfuse tylko jeśli jest włączony
#   
langfuse = None
if LANGFUSE_ENABLED:
    try:
        langfuse = get_client()
        if not langfuse:
            print("Ostrzeżenie: Nie udało się zainicjalizować klienta Langfuse")
    except Exception as e:
        print(f"Błąd podczas inicjalizacji Langfuse: {str(e)}")
else:
    print("Langfuse jest wyłączony")

#
# Tworzy nowy trace w Langfuse.
#
def create_trace(session_id: str, app_name: str = "yllia-mvp") -> str:
    """
    Tworzy nowy trace w Langfuse.
    
    Returns:
        trace_id (str)
    """
    if not LANGFUSE_ENABLED or not langfuse:
        return "mock_trace_id"

    try:
        with langfuse.start_as_current_span(name="chat-session") as root:
            root.update_trace(
                session_id=session_id,
                metadata={"app": app_name, "source": "streamlit"},
                tags=["yllia_feedback"]
            )
            return root.trace_id
    except Exception as e:
        print(f"Błąd podczas tworzenia trace: {str(e)}")
        return "mock_trace_id"

#
# Trackuje pojedyncze wywołanie LLM z pełnym kontekstem.
#
def track_generation_complete(
    trace_id: str,
    model: str,
    user_input: str,
    response_callback,
    ctx_static: str = "",
    ctx_dynamic: str = "",
    speech_history: str = ""
) -> tuple[str, str]:
    """
    Trackuje pojedyncze wywołanie LLM z pełnym kontekstem.
    
    Args:
        trace_id: ID trace'a
        model: nazwa modelu
        user_input: pytanie użytkownika
        ctx_static: kontekst statyczny (baza wiedzy)
        ctx_dynamic: kontekst dynamiczny (dane administracyjne)
        speech_history: historia rozmowy
        response_callback: funkcja wywołująca LLM, przyjmująca parametry (user_input, ctx_static, ctx_dynamic, speech_history)
        
    Returns:
        (response_text, observation_id)
    """
    if not LANGFUSE_ENABLED:
        return response_callback(user_input, ctx_static, ctx_dynamic, speech_history), None
    
    with langfuse.start_as_current_span(
        name="user-turn",
        trace_context={"trace_id": trace_id}
    ):
        with langfuse.start_as_current_generation(
            name="openai-call",
            model=model,
            input=user_input,
        ) as generation:
            response = response_callback(user_input, ctx_static, ctx_dynamic, speech_history)
            generation.update(output={"text": response})
            return response, generation.id


#
# Trackuje pojedyncze wywołanie LLM w trybie podstawowym (tylko historia rozmowy).
#
def track_generation_basic(
    trace_id: str,
    model: str,
    conversation: list[dict],
    response_callback
) -> tuple[str, str]:
    """
    Trackuje pojedyncze wywołanie LLM w trybie podstawowym (tylko historia rozmowy).
    
    Args:
        trace_id: ID trace'a
        model: nazwa modelu
        conversation: lista wiadomości w formacie [{"role": "user"|"assistant", "content": str}]
        response_callback: funkcja wywołująca LLM, przyjmująca parametr conversation
        
    Returns:
        (response_text, observation_id)
    """
    if not LANGFUSE_ENABLED:
        return response_callback(conversation), None
    
    with langfuse.start_as_current_span(
        name="user-turn",
        trace_context={"trace_id": trace_id}
    ):
        with langfuse.start_as_current_generation(
            name="openai-call",
            model=model,
            input=conversation,
        ) as generation:
            response = response_callback(conversation)
            generation.update(output={"text": response})
            return response, generation.id

#
# Zapisuje feedback użytkownika (👍/👎).
#
def create_feedback(
    trace_id: str,
    feedback_type: str,  # "up" | "down"
    observation_id: Optional[str] = None
):
    """
    Zapisuje feedback użytkownika (👍/👎).
    """
    if not LANGFUSE_ENABLED:
        return

    
    langfuse.create_score(
        name="user_feedback",
        data_type="CATEGORICAL",
        value=feedback_type,
        trace_id=trace_id,
        observation_id=observation_id
    )

#
# Zapisuje końcową ocenę sesji (1-5).
#
def create_session_rating(
    trace_id: str,
    rating: int,
    comment: str = ""
):
    """
    Zapisuje końcową ocenę sesji (1-5).
    """
    if not LANGFUSE_ENABLED:
        return None
    
    langfuse.create_score(
        name="session_feedback",
        data_type="NUMERIC",
        value=float(rating),
        trace_id=trace_id,
        comment=comment
    )
    langfuse.flush()