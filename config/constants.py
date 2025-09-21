APP_TITTLE = "Yllia - wirtualna asystentka"
APP_ICON = ":sparkles:"
APP_DESCRIPTION = "\n\n**Yllia** – wirtualna asystentka gabinetu psychiatrycznego."    
APP_DESCRIPTION += "\n\nPowstała, by w prosty i życzliwy sposób odpowiadać na najczęstsze pytania pacjentów."
APP_DESCRIPTION += "\n\nNie zastępuje lekarza ani rejestracji, ale pomaga odnaleźć się w tym, jak wygląda praca gabinetu i czego można się spodziewać przed wizytą."
APP_VERSION = "2.1.0 - testowa wersja"
APP_AUTHOR = "Damian Siwicki"
APP_AUTHOR_EMAIL = "poczta@siwicki.info"
APP_AUTHOR_WEBSITE = "https://siwicki.info"

WARNING_CONTENT = """
- **To nie są porady medyczne** – Yllia jest wirtualną asystentką edukacyjną, nie zastępuje konsultacji z lekarzem.  
- **W nagłych przypadkach** – Zadzwoń pod numer alarmowy **112** lub zgłoś się do najbliższego SOR.  
- **Wersja testowa** – Aplikacja znajduje się w fazie testów i może zawierać błędy.  
- **Cel aplikacji** – Yllia ma na celu wsparcie pacjentów w przygotowaniu się do wizyty w gabinecie.  
- **Ochrona danych** – Proszę nie podawać danych osobowych ani wrażliwych. Aplikacja nie służy do gromadzenia takich informacji, a wpisywane treści są przesyłane do systemów OpenAI w celu wygenerowania odpowiedzi.  
- **Weryfikacja informacji** – Zawsze skonsultuj otrzymane informacje z lekarzem lub farmaceutą.  

Korzystając z aplikacji, potwierdzasz, że rozumiesz i akceptujesz powyższe ograniczenia.
"""

OPENAI_MODEL = "gpt-4o-mini"

OPENAI_PRICING = {
    "gpt-4o": {
        "input_per_million": 2.50,  # USD
        "output_per_million": 10.00
    },
    "gpt-4o-mini": {
        "input_per_million": 0.15,
        "output_per_million": 0.60
    }
}

USD_TO_PLN = 3.63

YLLIA_FIRST_MESSAGE = "Cześć, jestem Yllia, z przyjemnością odpowiem na Twoje pytania."

MAX_TURNS = 3

EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSION = 3072
QDRANT_COLLECTION_NAME = "yllia_chat_bot"
QDRANT_COLLECTION_NAME_DYNAMIC = "yllia_dynamic_qna"

# Role w rozmowie
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"

# Nazwy kolekcji w Qdrant
COLLECTION_STATIC = "yllia_chat_bot"
COLLECTION_DYNAMIC = "yllia_dynamic_qna"

# Modele
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_DISTANCE = "Cosine"

# Supabase – nazwy tabel
TABLE_MESSAGES = "messages"
TABLE_SESSIONS = "sessions"
TABLE_FEEDBACK = "feedback"