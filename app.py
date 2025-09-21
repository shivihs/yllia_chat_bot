import os, uuid
import streamlit as st
from langfuse import get_client
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv
from openai import OpenAI
from config.constants import * # APP_TITTLE, APP_ICON, APP_DESCRIPTION, APP_VERSION, APP_AUTHOR, APP_AUTHOR_EMAIL, APP_AUTHOR_WEBSITE, OPENAI_MODEL, YLLIA_FIRST_MESSAGE, MAX_TURNS, EMBEDDING_MODEL, EMBEDDING_DIMENSION, QDRANT_COLLECTION_NAME
import services.langfuse_service as langfuse_service

from services.openai_service import ask_openai
import tiktoken
import services.prompt_sevice as prompt_service
from PIL import Image
import services.supabase_service as supabase_service
from services.conversation_service import summarize_full_history
from services.qdrant_service import search_embeddings


# Inicjalizacja st.session_state

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "trace_id" not in st.session_state:
    st.session_state.trace_id = langfuse_service.create_trace(st.session_state.session_id)

if "last_observation_id" not in st.session_state:
    st.session_state.last_observation_id = None

if "output_feedback_given" not in st.session_state:
    st.session_state.output_feedback_given = True

if "session_feedback_given" not in st.session_state:
    st.session_state.session_feedback_given = False

if "turns" not in st.session_state:
    st.session_state.turns = 0

if "terms_accepted" not in st.session_state:
    st.session_state.terms_accepted = False

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": YLLIA_FIRST_MESSAGE})


#
# Obsługa tokenów
#
if "token_total_count" not in st.session_state:
    st.session_state.token_total_count = 0
if "token_input_count" not in st.session_state:
    st.session_state.token_input_count = 0
if "token_output_count" not in st.session_state:
    st.session_state.token_output_count = 0   

#
# Obsługa nowej sesji
#
def new_messages():
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": YLLIA_FIRST_MESSAGE})

def reset_session():
    # Podsumowanie rozmowy
    chat_summary = ask_openai("Podsumuj proszę naszą rozmowę.", ctx_static="", ctx_dynamic="", speech_history=summarize_full_history(st.session_state.messages))
    st.session_state.input_count = len(tiktoken.encoding_for_model(OPENAI_MODEL).encode(summarize_full_history(st.session_state.messages)))
    st.session_state.output_count = len(tiktoken.encoding_for_model(OPENAI_MODEL).encode(chat_summary))
    st.session_state.token_total_count = st.session_state.input_count + st.session_state.output_count
    supabase_service.messages_new(st.session_state.session_id, "Podsumowanie rozmowy", "", "", "", OPENAI_MODEL, st.session_state.input_count, st.session_state.output_count, chat_summary)
    # Zakończenie sesji
    supabase_service.sessions_update(st.session_state.session_id, chat_summary=chat_summary)
    supabase_service.sessions_end(st.session_state.session_id)
    
    """Resetuje sesję i tworzy nowy trace."""
    st.session_state.session_id = str(uuid.uuid4())
    supabase_service.sessions_new(st.session_state.session_id)
    prompt_service.save_prompts_to_database(st.session_state.session_id) # zapisujemy prompty do bazy danych
    st.session_state.trace_id = langfuse_service.create_trace(st.session_state.session_id)
    new_messages()
    st.session_state.output_feedback_given = True
    st.session_state.session_feedback_given = False
    st.session_state.turns = 0
    st.session_state.last_observation_id = None


#
# Obsługa akceptacji warunków
#

with st.container():
    if st.session_state.terms_accepted:
        st.success(f"✅ **Warunki zakceptowane - możesz korzystać z aplikacji**\n\n {WARNING_CONTENT.strip()}")
    else:
        st.warning(f"**⚠️ Warunki korzystania z aplikacji Yllia:**\n\n {WARNING_CONTENT.strip()}")

# Przycisk akceptacji - tylko gdy nie zaakceptowano
if not st.session_state.terms_accepted:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✅ Rozumiem i akceptuję", use_container_width=True, type="secondary"):
            st.session_state.terms_accepted = True
            st.rerun()
    
    # Zatrzymaj renderowanie reszty aplikacji
    st.stop()

# Separator
st.markdown("---")

# Tutaj reszta Twojej aplikacji
st.subheader("💬 Chat z Yllią")

#
# Przy nowej sesji - przycisk rozpoczęcia nowej sesji
#

if st.session_state.session_feedback_given == True:
    if st.button("Rozpocznij nową sesję", use_container_width=True):
        st.session_state.session_feedback_given = False
        reset_session()
        st.rerun()
    else:
        st.stop()


#
# Obsługa czatu
#
def render_history():
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
render_history()


def ask_gpt(messages):
    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages
    )
    return response.choices[0].message.content


    
#
# Obsługa promptu użytkownika
#
if user_input := st.chat_input("Zadaj pytanie:"):
   
    # Jeśli nie przekroczyliśmy limitu, generujemy odpowiedź
    if st.session_state.turns < MAX_TURNS:
        
        # Dodajemy pytanie użytkownika do historii
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
        
        # Generujemy kontekst
        answer_static = search_embeddings(user_input, QDRANT_COLLECTION_NAME)[0].payload["answer"]
        answer_dynamic = search_embeddings(user_input, QDRANT_COLLECTION_NAME_DYNAMIC)[0].payload["answer"]
        conversation_summarized = summarize_full_history(st.session_state.messages)
       
        # Generujemy odpowiedź
        response, st.session_state.last_observation_id = langfuse_service.track_generation_complete(st.session_state.trace_id, OPENAI_MODEL, user_input, ask_openai, answer_static, answer_dynamic, conversation_summarized)
        
        # Dodajemy odpowiedź do historii i oznaczamy jako nieocenioną
        st.session_state.output_feedback_given = False
        st.session_state.messages.append({"role": "assistant", "content": response, "obs_id": st.session_state.last_observation_id})
        
        # Liczymy tokeny
        st.session_state.token_input_count = len(tiktoken.encoding_for_model(OPENAI_MODEL).encode(user_input + prompt_service.load_prompt(ctx_static=answer_static, ctx_dynamic=answer_dynamic, conversation_summarized=conversation_summarized)))
        st.session_state.token_input_count += len(tiktoken.encoding_for_model(OPENAI_MODEL).encode(user_input))
        st.session_state.token_output_count = len(tiktoken.encoding_for_model(OPENAI_MODEL).encode(st.session_state.messages[-1]["content"]))
        st.session_state.token_total_count += st.session_state.token_input_count + st.session_state.token_output_count
        
        # zapisujemy wiadomość do bazy danych
        supabase_service.messages_new(st.session_state.session_id, user_input, answer_static, answer_dynamic, conversation_summarized, OPENAI_MODEL, st.session_state.token_input_count, st.session_state.token_output_count, st.session_state.messages[-1]["content"])

        # Zwiększamy licznik tur
        st.session_state.turns += 1

        # Pokazujemy odpowiedź i przyciski oceny w tym samym kontenerze
        with st.chat_message("assistant"):
            st.write(response)
            
# Przyciski oceny bezpośrednio pod odpowiedzią
if not st.session_state.output_feedback_given:
    c1, c2 = st.columns(2)
    if c1.button("👍 Pomocne", key="up", use_container_width=True):
        langfuse_service.create_feedback(st.session_state.trace_id, "up", st.session_state.last_observation_id)
        supabase_service.messages_update_score(st.session_state.session_id, True)
        st.toast("Dzięki za feedback! 👍", icon="✅")
        st.session_state.output_feedback_given = True
        st.rerun()
    if c2.button("👎 Niepomocne", key="down", use_container_width=True):
        langfuse_service.create_feedback(st.session_state.trace_id, "down", st.session_state.last_observation_id)
        supabase_service.messages_update_score(st.session_state.session_id, False)
        st.toast("Dzięki za feedback! 👎", icon="✅")
        st.session_state.output_feedback_given = True
        st.rerun()
#
# Feedback końcowy po osiągnięciu limitu
#
if st.session_state.turns >= MAX_TURNS:
    st.markdown("---")
    # Pokazujemy expander zawsze po osiągnięciu limitu, jeśli rozmowa nie została jeszcze oceniona
    if not st.session_state.session_feedback_given:
        st.warning(
            f"Przekroczono limit {MAX_TURNS} pytań w tej sesji. "
            "Dziękuję za rozmowę! Proszę o ocenę ostatniej odpowiedzi oraz całej rozmowy poniżej. 🙏"
        )
        with st.expander("Oceń całą rozmowę", expanded=True):
            session_feedback_rating = st.slider(
                "Twoja ocena od 1 (słabo) do 5 (super)", 
                1, 5, 5, 
                help="1 - słabo, 5 = super"
            )
            session_feedback_comment = st.text_input("Komentarz (opcjonalnie)")
            
            if st.button("Zakończ i oceń", use_container_width=True):
                langfuse_service.create_session_rating(
                    st.session_state.trace_id, 
                    session_feedback_rating, 
                    session_feedback_comment
                )
                st.session_state.session_feedback_given = True
                st.toast("Dziękuję za ocenę rozmowy! 🌟", icon="✅")
                st.rerun()

