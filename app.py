import os, uuid
import streamlit as st
from langfuse import get_client
from dotenv import load_dotenv
from openai import OpenAI
from config.constants import APP_TITTLE, APP_ICON, APP_DESCRIPTION, APP_VERSION, APP_AUTHOR, APP_AUTHOR_EMAIL, APP_AUTHOR_WEBSITE, OPENAI_MODEL, YLLIA_FIRST_MESSAGE, MAX_TURNS
import time
# Inicjalizacja zmiennych sekretnych
load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

langfuse = get_client()

# Konfiguraca strony

st.set_page_config(
    page_title=APP_TITTLE, 
    page_icon=APP_ICON, 
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        "about": f"{APP_DESCRIPTION}\n\n**v.{APP_VERSION}**\n\n{APP_AUTHOR}\n\n{APP_AUTHOR_EMAIL}\n\n{APP_AUTHOR_WEBSITE}"
    }
    )

st.title(f"{APP_ICON} {APP_TITTLE}")

st.sidebar.title("ℹ️ Informacje")
st.sidebar.markdown(f"**Opis:** {APP_DESCRIPTION}")
st.sidebar.markdown(f"**Wersja:** {APP_VERSION}")
st.sidebar.markdown(f"**Autor:** {APP_AUTHOR}")
st.sidebar.markdown(f"**{APP_AUTHOR_EMAIL}**")
st.sidebar.markdown(f"**{APP_AUTHOR_WEBSITE}**")

# Inicjalizacja st.session_state

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "trace_id" not in st.session_state:
    with langfuse.start_as_current_span(name="chat-session") as root:
        root.update_trace(
            session_id=st.session_state.session_id,
            metadata={"app": "yllia-demo", "source": "streamlit"},
            tags=["yllia", "demo"]
        )
        st.session_state.trace_id = root.trace_id
if "last_observation_id" not in st.session_state:
    st.session_state.last_observation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": YLLIA_FIRST_MESSAGE})
if "feedback_given" not in st.session_state:
    st.session_state.feedback_given = True
if "session_feedback_given" not in st.session_state:
    st.session_state.session_feedback_given = False
if "session_rating" not in st.session_state:
    st.session_state.session_rating = 5
if "session_comment" not in st.session_state:
    st.session_state.session_comment = ""
if "turns" not in st.session_state:
    st.session_state.turns = 0
if "begin_session" not in st.session_state:
    st.session_state.begin_session = True

#
# Obsługa nowego trace'a - FUNKCJA PRYWATNA
#
def _new_trace():
    st.session_state.trace_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": YLLIA_FIRST_MESSAGE})
    st.session_state.feedback_given = True
    st.session_state.session_feedback_given = False
    st.session_state.session_rating = 5
    st.session_state.session_comment = ""
    st.session_state.turns = 0
    st.session_state.last_observation_id = None
    
    with langfuse.start_as_current_span(name="chat-session") as root:
        root.update_trace(
            session_id=st.session_state.session_id,
            metadata={"app": "yllia-demo", "source": "streamlit"},
            tags=["yllia", "demo"]
        )
        st.session_state.trace_id = root.trace_id

#
# Przy nowej sesji - przycisk rozpoczęcia nowej sesji
#

if st.session_state.begin_session == False:
    if st.button("Rozpocznij nową sesję", use_container_width=True):
        st.session_state.begin_session = True
        _new_trace()
        st.rerun()
    else:
        st.stop()


# if not st.session_state.begin_session:
#     st.stop()


#
# Obsługa historii
#
def render_history():
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
render_history()

#
# Obsługa span
#
def ask_gpt(messages):
    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages
    )
    return response.choices[0].message.content


def handle_turn(user_input: str) -> tuple[str, str]:
    with langfuse.start_as_current_span(
        name="user-turn",
        trace_context={"trace_id": st.session_state.trace_id}
    ):
        conversation = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.messages]
        # conversation.append({"role": "user", "content": user_input})

        with langfuse.start_as_current_generation(
            name="openai-call",
            model=OPENAI_MODEL,
            input=conversation,
        ) as generation:
            response = ask_gpt(conversation)
            generation.update(output={"text": response})
            generation.end()
            st.session_state.last_observation_id = generation.id
            st.session_state.feedback_given = False
            return response, generation.id
        
#
# Obsługa promptu użytkownika
#

if prompt := st.chat_input("Zadaj pytanie:"):
    
    if st.session_state.turns >= MAX_TURNS and not st.session_state.session_feedback_given:
        st.warning(
            f"Przekroczono limit {MAX_TURNS} pytań w tej sesji. "
            "Dziękuję za rozmowę! Proszę o końcową ocenę poniżej, a następnie rozpoczniemy nową sesję. 🙏"
        )
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        response, obs_id = handle_turn(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response, "obs_id": obs_id})
        with st.chat_message("assistant"):
            st.write(response)
        st.session_state.turns += 1


#
# Obsługa feedbacku
#
ph = st.empty()

if st.session_state.feedback_given == False:
    with ph.container():
        c1, c2 = st.columns(2)
        if c1.button("👍 Pomocne", key=f"up", use_container_width=True):
            langfuse.create_score(
                name="user_feedback",
                data_type="CATEGORICAL",
                value="up",
                trace_id=st.session_state.trace_id,
                observation_id=st.session_state.last_observation_id
            )
            st.toast("Dzięki za feedback! 👍", icon="✅")
            st.session_state.feedback_given = True
        if c2.button("👎 Niepomocne", key=f"down", use_container_width=True):
            langfuse.create_score(
                name="user_feedback",
                data_type="CATEGORICAL",
                value="down",
                trace_id=st.session_state.trace_id,
                observation_id=st.session_state.last_observation_id
            )
            st.toast("Dzięki za feedback! 👎", icon="✅")
            st.session_state.feedback_given = True
        if st.session_state.feedback_given:
            ph.empty()

#
# Feedback zbiorczy
#

st.markdown("---")
if st.session_state.session_feedback_given == False:
        
    with st.expander("Oceń rozmowę.", expanded=False):
        feedback_rating = st.slider("Twoja ocena od 1 (słabo) do 5 (super)", 1, 5, 5, help="1 - słabo, 5 = super")
        feedback_comment = st.text_input("Komentarz(opcjonalnie)")
        if st.button("Oceń", use_container_width=True):
            langfuse.create_score(
                name="session_feedback",
                data_type="NUMERIC",
                value=float(feedback_rating),
                trace_id=st.session_state.trace_id,
                comment=feedback_comment
            )
            langfuse.flush()
            st.session_state.session_feedback_given = True
            st.toast("Dziękuję za feedback!", icon="✅")
            st.session_state.begin_session = False
            st.rerun()

# ---------- Render historii ----------
# for i, msg in enumerate(st.session_state.messages):
#     with st.chat_message(msg["role"]):
#         st.write(msg["content"])

#     # Tylko dla asystenta: pokaż feedback jeśli nie oceniono
#     if msg["role"] == "assistant" and "obs_id" in msg and msg["obs_id"] not in st.session_state.rated_obs_ids:
#         ph = st.empty()
#         with ph.container():
#             c1, c2 = st.columns(2)
#             if c1.button("👍 Pomocne", key=f"up_{i}", use_container_width=True):
#                 langfuse.create_score(
#                     name="user_feedback",
#                     data_type="CATEGORICAL",
#                     value="up",
#                     trace_id=st.session_state.trace_id,
#                     observation_id=msg["obs_id"]
#                 )
#                 st.session_state.rated_obs_ids.add(msg["obs_id"])
#                 st.toast("Dzięki za feedback! 👍", icon="👍")
#                 ph.empty()
#             if c2.button("👎 Niepomocne", key=f"down_{i}", use_container_width=True):
#                 langfuse.create_score(
#                     name="user_feedback",
#                     data_type="CATEGORICAL",
#                     value="down",
#                     trace_id=st.session_state.trace_id,
#                     observation_id=msg["obs_id"]
#                 )
#                 st.session_state.rated_obs_ids.add(msg["obs_id"])
#                 st.toast("Dzięki za feedback! 👎", icon="👎")
#                 ph.empty()