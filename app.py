import uuid
import streamlit as st
from config.constants import * # APP_TITTLE, APP_ICON, APP_DESCRIPTION, APP_VERSION, APP_AUTHOR, APP_AUTHOR_EMAIL, APP_AUTHOR_WEBSITE, OPENAI_MODEL, YLLIA_FIRST_MESSAGE, MAX_TURNS, EMBEDDING_MODEL, EMBEDDING_DIMENSION, QDRANT_COLLECTION_NAME
import services.langfuse_service as langfuse_service
from PIL import Image
from services.openai_service import ask_openai
import tiktoken
import services.prompt_sevice as prompt_service
from PIL import Image
import services.supabase_service as supabase_service
from services.conversation_service import summarize_full_history, summarize_full_history_for_patients, check_length, translate_from_polish, detect_and_translate_to_polish, LanguageTracker
from services.qdrant_service import search_embeddings


#
# Podstawowe informacj o aplikacji
#
st.title(f"{APP_ICON} {APP_TITTLE}")

st.set_page_config(
    page_title=APP_TITTLE, 
    page_icon=APP_ICON, 
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        "about": f"{APP_DESCRIPTION}\n\n**v.{APP_VERSION}**\n\n{APP_AUTHOR}\n\n{APP_AUTHOR_EMAIL}\n\n{APP_AUTHOR_WEBSITE}"
    }
    )

#
# Funkcje pomocnicze
#
def reset_messages():
    # Resetuje historię wiadomości i język.
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": YLLIA_FIRST_MESSAGE})

def reset_languages():
    # Resetuje język.
    st.session_state.session_language.clear()

def reset_token_counts():
    # Resetuje liczniki tokenów.
    st.session_state.token_total_count = 0
    st.session_state.token_input_count = 0
    st.session_state.token_output_count = 0

def new_session():
    # Tworzy nową sesję.
    st.session_state.session_id = str(uuid.uuid4())

def initialize_session_in_db():
    # Zapisuje sesję do bazy danych przy pierwszej interakcji użytkownika
    supabase_service.sessions_new(st.session_state.session_id)
    prompt_service.save_prompts_to_database(st.session_state.session_id)

def new_trace():
    # Tworzy nowy trace.
    st.session_state.trace_id = langfuse_service.create_trace(st.session_state.session_id)

def finalize_session(final_score: int = None, final_note: str = ""):
    # Zamyka sesję.
    #st.session_state.token_input_count - nic nie robimy - już policzone przy generowaniu podsumowania dla pacjenta
    # Liczymy tokeny
    st.session_state.token_output_count = len(tiktoken.encoding_for_model(OPENAI_MODEL).encode(st.session_state.session_summary))
    st.session_state.token_total_count += st.session_state.token_input_count + st.session_state.token_output_count
    # Zapisujemy podsumowanie rozmowy do bazy danych i zamykamy sesję
    supabase_service.messages_add(st.session_state.session_id, "Podsumowanie rozmowy", "", "", "", OPENAI_MODEL, st.session_state.token_input_count, st.session_state.token_output_count, st.session_state.session_summary, st.session_state.session_language.get_dominant_language())
    supabase_service.sessions_update(st.session_state.session_id, chat_summary=st.session_state.session_summary, score_final=final_score, score_note=final_note, usage_total=st.session_state.token_total_count)
    supabase_service.sessions_end(st.session_state.session_id)

    
def reset_session(final_score: int = None, final_note: str = ""):
    # Resetuje sesję - funkcja pomocnicza (komentarz po polsku, nie wyświetla się w aplikacji). 
    finalize_session(final_score, final_note)
    reset_messages()
    reset_languages()
    reset_token_counts()
    # Tworzymy nową sesję (ale nie zapisujemy od razu do bazy)
    new_session()
    # Resetujemy stan sesji
    st.session_state.trace_id = None
    st.session_state.session_initialized = False
    st.session_state.output_feedback_given = True # Musi być True - żeby nie było opcji oceny pierwszej wiadomośći od Yllii
    st.session_state.turns = 0
    st.session_state.last_observation_id = None ## To reset dla langfuse
    st.session_state.session_summary = "" ## To reset dla podsumowania
    st.session_state.session_summary_generated = False

    
#
# Inicjalizacja st.session_state
#

# Identyfikatory
if "session_id" not in st.session_state:
    new_session()
if "trace_id" not in st.session_state:
    # Tworzymy trace tylko gdy użytkownik faktycznie zaczyna interakcję
    # Nie od razu przy przeładowaniu aplikacji
    st.session_state.trace_id = None
if "session_initialized" not in st.session_state:
    # Flaga czy sesja została już zapisana do bazy danych
    st.session_state.session_initialized = False
if "last_observation_id" not in st.session_state:
    st.session_state.last_observation_id = None

# Różne stany sesji
if "turns" not in st.session_state:
    st.session_state.turns = 0
if "messages" not in st.session_state:
    reset_messages()
if "image" not in st.session_state:
    st.session_state.image = Image.open("assets/yllia_profile.png")
if "session_summary" not in st.session_state:
    st.session_state.session_summary = ""
if "session_language" not in st.session_state:
    st.session_state.session_language = LanguageTracker()

# Flagi
if "session_summary_generated" not in st.session_state: # Na koniec, aby nie generowało się podsumowanie wielokrotnie
    st.session_state.session_summary_generated = False
if "terms_accepted" not in st.session_state:
    st.session_state.terms_accepted = False    
if "output_feedback_given" not in st.session_state:
    st.session_state.output_feedback_given = True # Musi być True - żeby nie było opcji oceny pierwszej wiadomośći od Yllii 
if "session_feedback_given" not in st.session_state:
    st.session_state.session_feedback_given = False

# Obsługa tokenów
if "token_total_count" not in st.session_state:
    st.session_state.token_total_count = 0
if "token_input_count" not in st.session_state:
    st.session_state.token_input_count = 0
if "token_output_count" not in st.session_state:
    st.session_state.token_output_count = 0   

#
# Obsługa nowej sesji
#


#
# Obsługa sidebar
#
with st.sidebar:
    st.subheader(f"{APP_ICON} {APP_TITTLE}")
    st.image(st.session_state.image, width=300)
    st.subheader("ℹ️ Informacje")
    st.markdown(f"{APP_DESCRIPTION}")
    st.markdown(f"**Języki:** {' | '.join(SUPPORTED_LANGUAGES.keys())}")
    st.markdown(f"**Wersja:** {APP_VERSION}")
    st.markdown(f"**Autor:** {APP_AUTHOR}")
# st.sidebar.markdown(f"**{APP_AUTHOR_EMAIL}**")
    st.markdown(f"**{APP_AUTHOR_WEBSITE}**")

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
# Przycisk znika po kliknięciu, placeholder czyści się natychmiast
placeholder = st.empty()
if st.session_state.session_feedback_given:
    with placeholder:
        if st.button("Rozpocznij nową sesję", use_container_width=True):
            st.session_state.session_feedback_given = False
            placeholder.empty()
        else:
            st.stop()


#
# Obsługa czatu
#
def render_history():
    """
    Wyświetla historię czatu z niestandardowymi awatarami.
    """

    for i, msg in enumerate(st.session_state.messages):
        avatar = AVATARS.get(msg["role"], "💬")  # Domyślny awatar jeśli nieznana rola
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])

render_history()


    
#
# Obsługa promptu użytkownika
#
if user_input := st.chat_input("Zadaj pytanie:"):
    if not check_length(user_input):
        st.error(f"Maksymalna długość wiadomości to {MAX_INPUT} znaków.")
        st.stop()
    else:
        pass
    # Jeśli nie przekroczyliśmy limitu, generujemy odpowiedź
    if st.session_state.turns < MAX_TURNS:
        
        # Dodajemy pytanie użytkownika do historii
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar=AVATARS["user"]):
            st.write(user_input)
        
        user_input, language, token_count = detect_and_translate_to_polish(user_input)
        st.session_state.session_language.add_language(language)
        st.session_state.token_total_count += token_count

        with st.spinner("Myślę nad odpowiedzią..."):       # Generujemy kontekst
            answer_static = search_embeddings(user_input, QDRANT_COLLECTION_NAME)[0].payload["answer"]
            answer_dynamic = search_embeddings(user_input, QDRANT_COLLECTION_NAME_DYNAMIC)[0].payload["answer"]
            st.session_state.session_summary, tokens_temp_input_count = summarize_full_history(st.session_state.messages)
            st.session_state.token_total_count += tokens_temp_input_count
            
            # Inicjalizujemy sesję i trace przy pierwszej interakcji użytkownika
            if not st.session_state.session_initialized:
                initialize_session_in_db()
                st.session_state.session_initialized = True
            
            if st.session_state.trace_id is None:
                new_trace()
            
            # Generujemy odpowiedź z spinnerem
            response, st.session_state.last_observation_id = langfuse_service.track_generation_complete(st.session_state.trace_id, OPENAI_MODEL, user_input, ask_openai, answer_static, answer_dynamic, st.session_state.session_summary)
        
            # Jeżeli ostatnio dodany język to nie polski, tłumaczemy odpowiedź
            if st.session_state.session_language.last_added() != "pl":
                response, token_count = translate_from_polish(response, st.session_state.session_language.last_added())
                st.session_state.token_total_count += token_count

        # Dodajemy odpowiedź do historii i oznaczamy jako nieocenioną
        st.session_state.output_feedback_given = False
        st.session_state.messages.append({"role": "assistant", "content": response, "obs_id": st.session_state.last_observation_id})
        
        # Liczymy tokeny
        st.session_state.token_input_count = len(tiktoken.encoding_for_model(OPENAI_MODEL).encode(user_input + prompt_service.load_prompt(ctx_static=answer_static, ctx_dynamic=answer_dynamic, conversation_summarized=st.session_state.session_summary)))
        st.session_state.token_input_count += len(tiktoken.encoding_for_model(OPENAI_MODEL).encode(user_input))
        st.session_state.token_output_count = len(tiktoken.encoding_for_model(OPENAI_MODEL).encode(st.session_state.messages[-1]["content"]))
        st.session_state.token_total_count += st.session_state.token_input_count + st.session_state.token_output_count
        
        # zapisujemy wiadomość do bazy danych
        supabase_service.messages_add(st.session_state.session_id, user_input, answer_static, answer_dynamic, st.session_state.session_summary, OPENAI_MODEL, st.session_state.token_input_count, st.session_state.token_output_count, st.session_state.messages[-1]["content"], language)

        # Zwiększamy licznik tur
        st.session_state.turns += 1

        # Pokazujemy odpowiedź i przyciski oceny w tym samym kontenerze
        with st.chat_message("assistant", avatar=AVATARS["assistant"]):
            st.write(response)


            
# Przyciski oceny bezpośrednio pod odpowiedzią
if not st.session_state.output_feedback_given:
    c1, c2 = st.columns(2)
    if c1.button("👍 Pomocne", key="up", use_container_width=True):
        st.toast("Dzięki za feedback! 👍", icon="✅")
        langfuse_service.create_feedback(st.session_state.trace_id, "up", st.session_state.last_observation_id)
        supabase_service.messages_update_score(st.session_state.session_id, True)
        st.session_state.output_feedback_given = True
        st.rerun()
    if c2.button("👎 Niepomocne", key="down", use_container_width=True):
        st.toast("Dzięki za feedback! 👎", icon="✅")
        langfuse_service.create_feedback(st.session_state.trace_id, "down", st.session_state.last_observation_id)
        supabase_service.messages_update_score(st.session_state.session_id, False)
        st.session_state.output_feedback_given = True
        st.rerun()
#
# Feedback końcowy po osiągnięciu limitu
#
if st.session_state.turns >= MAX_TURNS:
    st.markdown("---")
    # Pokazujemy expander zawsze po osiągnięciu limitu, jeśli rozmowa nie została jeszcze oceniona
    if not st.session_state.session_feedback_given:
        if MAX_TURNS == 1:
            st.warning(
            f"Osiągnięto limit {MAX_TURNS} pytań w tej sesji. "
            "Dziękuję za rozmowę i poproszę o ocenę podsumowującą. 🙏 \n\nPo przesłaniu oceny możliwe będzie rozpoczęcie nowej sesji."
            )
        else:
            st.warning(
            f"Dziękuję za rozmowę i poproszę o opinię podsumowującą. 🙏 \n\nPo przesłaniu oceny możliwe będzie rozpoczęcie nowej sesji."
            )
        if not st.session_state.session_summary_generated:
            st.session_state.session_summary, st.session_state.token_input_count = summarize_full_history_for_patients(st.session_state.messages, st.session_state.session_summary)
            st.session_state.session_summary_generated = True
            if st.session_state.session_language.get_dominant_language() != "pl" and st.session_state.session_language.get_dominant_language() != "unknown":
                st.session_state.session_summary, token_count = translate_from_polish(st.session_state.session_summary, st.session_state.session_language.get_dominant_language())
                st.session_state.token_total_count += token_count
        st.success(f"📝**Podsumowanie**\n\n{st.session_state.session_summary}")
        with st.expander("Podziel się swoją opinią", expanded=True):
            session_feedback_rating = st.slider(
                "💡 Twoja ocena od 1 (słabo) do 5 (super):", 
                1, 5, 5, 
                help="1 - słabo, 5 - super"
            )
            session_feedback_comment = st.text_input("🖊️ Komentarz:", value="", placeholder="Dodaj kilka słów od siebie… (opcjonalnie)")[:500]
            if st.button("✅ Prześlij opinię", use_container_width=True):
                langfuse_service.create_session_rating(
                    st.session_state.trace_id, 
                    session_feedback_rating, 
                    session_feedback_comment
                )
                st.toast("Dziękuję za opinię! 💡", icon="✅")
                st.session_state.session_feedback_given = True
                reset_session(session_feedback_rating, session_feedback_comment)
                st.rerun()

# Tuż po obsłudze akceptacji warunków i przed renderowaniem historii
if st.session_state.turns < MAX_TURNS and st.session_state.turns > 0 and not st.session_state.session_feedback_given:
    st.markdown("---")
    if st.button("📝 Zakończ i zobacz podsumowanie", use_container_width=True, type="secondary"):
        st.session_state.turns = MAX_TURNS + 1  # Symuluj osiągnięcie limitu + 1 - żeby dać znać, że użytkownik chce zakończyć sesję wcześniej
        st.rerun()


with st.sidebar:
    st.markdown("---")
    tekst = st.text_input("Podaj tekst w języku obcym do tłumaczenia:", value="", placeholder="Dodaj tekst do tłumaczenia...")
    if st.button("Na polski", use_container_width=True):
        tekst, język, token_count = detect_and_translate_to_polish(tekst)
        st.success(f"Tłumaczenie: {tekst}")
        st.success(f"Język: {język}")
        st.success(f"Liczba tokenów: {token_count}")
    tekst = st.text_input("Podaj tekst do tłumaczenia:", value="", placeholder="Dodaj tekst do tłumaczenia...")
    if st.button("Z polski", use_container_width=True):
        st.write()
        translated_text, token_count = translate_from_polish(tekst, "en")
        st.success(f"Tłumaczenie: {translated_text}")
        st.success(f"Liczba tokenów: {token_count}")