import os, uuid
import streamlit as st
from langfuse import get_client
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv
from openai import OpenAI
from config.constants import * # APP_TITTLE, APP_ICON, APP_DESCRIPTION, APP_VERSION, APP_AUTHOR, APP_AUTHOR_EMAIL, APP_AUTHOR_WEBSITE, OPENAI_MODEL, YLLIA_FIRST_MESSAGE, MAX_TURNS, EMBEDDING_MODEL, EMBEDDING_DIMENSION, QDRANT_COLLECTION_NAME


# Inicjalizacja zmiennych sekretnych
load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
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

#
# Obsługa embedingów
#

def get_embeddings(text):
    result = openai_client.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL,
        dimensions=EMBEDDING_DIMENSION,
    )
    return result.data[0].embedding

def search_embeddings(text, collection_name):
    results = qdrant_client.search(
        collection_name=collection_name,
        query_vector=get_embeddings(text),
        limit=3,
    )
    return results

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


def ask_chad_embeddings_responses(prompt: str, embedding: str, embedding_dynamic: str):
    ctx_static = embedding or ""
    ctx_dynamic = embedding_dynamic or ""

    input_text = (
        PROMPT_GENERAL + "\n\n"
        "# ROLA I TOŻSAMOŚĆ\n"
        "Jesteś Yllia, profesjonalną wirtualną asystentką gabinetu psychiatrycznego dra Damiana Siwickiego. "
        "Odpowiadasz WYŁĄCZNIE w języku polskim.\n\n"
        
        "# GŁÓWNE ZASADY ODPOWIADANIA\n"
        "1. **ZAWSZE analizuj oba konteksty przed odpowiedzią** - zarówno statyczny jak i dynamiczny zawierają kluczowe informacje\n"
        "2. **Odpowiadaj szczegółowo i kompletnie** - wykorzystuj wszystkie dostępne informacje z kontekstów\n"
        "3. **Cytuj konkretne informacje** z kontekstu, gdy są dostępne\n"
        "4. **Łącz informacje** z obu kontekstów, jeśli uzupełniają się\n"
        "5. Bądź **ciepła, empatyczna i pomocna** przy zachowaniu profesjonalizmu\n\n"
        
        "# HIERARCHIA INFORMACJI\n"
        "- **KONTEKST DYNAMICZNY**: dane administracyjne, godziny, kontakt, ceny - ZAWSZE AKTUALNE\n"
        "- **KONTEKST STATYCZNY**: odpowiedzi na częste pytania pacjentów - sprawdzone informacje\n"
        "- Jeśli informacje się różnią, priorytet ma kontekst dynamiczny\n"
        "- Jeśli nie wywnioskujesz inaczej, to priorytet ma kierowanie kontaktu na rejestrację poszczególnych gabinetów gdzie przyjmuje lekarz\n\n"
        
        "# INSTRUKCJE ODPOWIADANIA\n"
        "## Gdy masz informacje w kontekście:\n"
        "- Udziel pełnej, szczegółowej odpowiedzi\n"
        "- Wykorzystaj WSZYSTKIE istotne informacje z kontekstów\n"
        "- Dodaj praktyczne wskazówki, jeśli są w kontekście\n"
        "- Jeśli w kontekście są numery telefonów, godziny, ceny - podaj je\n\n"
        
        "## Gdy brakuje informacji:\n"
        "Odpowiedz: 'Niestety, nie mam tej informacji w mojej bazie danych. Polecam skontaktować się bezpośrednio z gabinetem.'\n\n"
        
        "## Pytania poza zakresem:\n"
        "- **Kryzysy psychiczne**: 'W sytuacjach kryzysowych proszę skontaktować się z Pogotowiem Ratunkowym (112) lub najbliższym szpitalem psychiatrycznym.'\n"
        "- **Tematy niezwiązane z gabinetem**: 'Jestem asystentką gabinetu psychiatrycznego i odpowiadam tylko na pytania związane z naszymi usługami.'\n"
        "- **Prywatne sprawy doktora**: 'Nie mogę udzielać informacji o sprawach prywatnych.'\n\n"
        
        "# PRZYKŁAD DOBREJ ODPOWIEDZI\n"
        "Zamiast: 'Tak, przyjmujemy pacjentów.'\n"
        "Napisz: 'Tak, dr Damian Siwicki prowadzi konsultacje psychiatryczne. Gabinet przyjmuje [dni/godziny z kontekstu]. Wizytę można umówić telefonicznie pod numerem [numer z kontekstu] lub [inne sposoby z kontekstu]. Koszt konsultacji to [cena z kontekstu].'\n\n"
        
        "---\n\n"
        "### KONTEKST STATYCZNY (odpowiedzi na częste pytania pacjentów):\n" + ctx_static + "\n\n"
        "### KONTEKST DYNAMICZNY (aktualne dane administracyjne gabinetu):\n" + ctx_dynamic + "\n\n"
        "### PYTANIE PACJENTA:\n" + prompt + "\n\n"
        
        "**Przeanalizuj oba konteksty, sprawdź czy to nie jest sytuacja nagła lub nieodpowiednia, a następnie udziel kompletnej, pomocnej odpowiedzi wykorzystując wszystkie dostępne informacje.**"
    )
    with st.sidebar:
        st.write(prompt)
    resp = openai_client.responses.create(
        model=OPENAI_MODEL,  # np. "o4-mini" / "o3"
        input=input_text,
        temperature=0.2,
    )
    # Tekstowy output jest zwykle pod resp.output_text
    return getattr(resp, "output_text", "").strip()

try:
    st.caption(st.session_state.messages[-2]["content"])

    search_qdrant = search_embeddings(st.session_state.messages[-2]["content"], QDRANT_COLLECTION_NAME)

    for result in search_qdrant:
        st.write(result.score, '...', result.payload["answer"])

    search_qdrant_dynamic = search_embeddings(st.session_state.messages[-2]["content"], QDRANT_COLLECTION_NAME_DYNAMIC)
    for result in search_qdrant_dynamic:
        st.write(result.score, '...', result.payload["answer"])
    
    st.write("Odpowiedź z Qdrant:")
    response = ask_chad_embeddings_responses(st.session_state.messages[-2]["content"], search_qdrant[0].payload["answer"], search_qdrant_dynamic[0].payload["answer"])
    st.write(response)
except:
    pass

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