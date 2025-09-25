# ✨ Yllia – wirtualna asystentka gabinetu psychiatrycznego

Yllia to profesjonalna wirtualna asystentka gabinetu psychiatrycznego.  
Powstała, aby w prosty, życzliwy i zrozumiały sposób odpowiadać na najczęstsze pytania pacjentów.  
Nie zastępuje lekarza ani rejestracji, ale pomaga odnaleźć się w organizacji pracy gabinetu oraz przygotować się do wizyty.

**Wersja:** 2.1 (testowa)  
**Autor:** Damian Siwicki

👉 [Zobacz pełną historię zmian](./CHANGELOG.md)

---

## ✨ Główne funkcjonalności

### 🔄 System sesyjny
- **Limit pytań**: Maksymalnie 7 pytania na sesję
- **Inteligentne podsumowania**: Automatyczne streszczanie historii rozmowy
- **Notatki dla pacjenta**: Czytelne podsumowanie po zakończeniu sesji
- **Akceptacja warunków**: Obowiązkowe zapoznanie się z zasadami korzystania

### 🧠 Inteligentne odpowiedzi
- **Podwójny kontekst**: Łączenie informacji statycznych (FAQ) i dynamicznych (aktualności)
- **RAG (Retrieval Augmented Generation)**: Wyszukiwanie w bazie wiedzy poprzez embeddingi
- **Priorytetyzacja**: Kontekst dynamiczny ma pierwszeństwo przed statycznym
- **Kompletność**: Wykorzystanie wszystkich dostępnych informacji z kontekstu

### 📊 Monitoring i feedback
- **System ocen**: Thumbs up/down dla każdej odpowiedzi
- **Ocena sesji**: Skala 1-5 z opcjonalnym komentarzem na koniec
- **Śledzenie tokenów**: Precyzyjne liczenie kosztów OpenAI
- **Pełna obserwowalność**: Integracja z Langfuse

### 🛡️ Bezpieczeństwo
- **Wykrywanie kryzysów**: Automatyczne kierowanie do służb ratunkowych (112)
- **Ograniczenia tematyczne**: Odpowiedzi wyłącznie w zakresie gabinetu
- **Ochrona danych**: Jasne komunikaty o przetwarzaniu danych przez OpenAI
- **Walidacja granic**: Uprzejme wyznaczanie ram rozmowy

---

## 🏗️ Architektura techniczna

### 🔄 Przepływ danych
1. **Akceptacja warunków** – obowiązkowe przed rozpoczęciem
2. **Inicjalizacja sesji** – utworzenie UUID i trace w Langfuse
3. **Przetwarzanie pytania**:
   - Generowanie embeddingu (OpenAI `text-embedding-3-large`)
   - Wyszukiwanie w Qdrant (kolekcje statyczna i dynamiczna)
   - Streszczenie historii rozmowy
4. **Generowanie odpowiedzi** – OpenAI `gpt-4o-mini` z pełnym kontekstem
5. **Zapis do bazy** – Supabase (sesje, wiadomości, feedback)
6. **Monitoring** – Langfuse (traces, generations, scores)
7. **Finalizacja sesji** – podsumowanie dla pacjenta i zamknięcie

### 📂 Struktura projektu
```
yllia_app/
├── app.py                      # główna aplikacja Streamlit
├── config/
│   ├── config.py              # konfiguracja środowiskowa (.env)
│   └── constants.py           # stałe globalne
├── services/
│   ├── openai_service.py      # komunikacja z OpenAI
│   ├── langfuse_service.py    # observability i monitoring
│   ├── supabase_service.py    # baza danych relacyjna
│   ├── qdrant_service.py      # baza wektorowa (embeddingi)
│   ├── conversation_service.py # streszczanie rozmów
│   └── prompt_sevice.py       # zarządzanie promptami
├── prompts/
│   ├── prompt_general.md      # główny prompt Yllii
│   ├── prompt_summary.md      # streszczanie historii
│   └── prompt_patients_summary.md # notatki dla pacjentów
└── assets/
    └── yllia_profile.png      # awatar w aplikacji
```

---

## 🗄️ Bazy danych

### Supabase - tabele
#### `yllia_sessions`
| Kolumna | Typ | Opis |
|---------|-----|------|
| id | bigint | klucz główny |
| session_id | uuid | identyfikator sesji |
| started_at | timestampz | rozpoczęcie sesji |
| ended_at | timestampz | zakończenie sesji |
| score_final | smallint | ocena końcowa (1-5) |
| score_note | text | komentarz użytkownika |
| chat_summary | text | podsumowanie rozmowy |
| usage_total | int | łączna liczba tokenów |

#### `yllia_messages`  
| Kolumna | Typ | Opis |
|---------|-----|------|
| id | bigint | klucz główny |
| session_id | uuid | powiązanie z sesją |
| user_input | text | pytanie pacjenta |
| context_static | jsonb | kontekst statyczny (FAQ) |
| context_dynamic | jsonb | kontekst dynamiczny |
| context_history | text | streszczona historia |
| chat_output | text | odpowiedź Yllii |
| score_up_down | boolean | ocena odpowiedzi (👍/👎) |
| model | text | użyty model OpenAI |
| usage_input | smallint | tokeny wejściowe |
| usage_output | smallint | tokeny wyjściowe |
| created_at | timestampz | czas utworzenia |

#### `yllia_prompts`
| Kolumna | Typ | Opis |
|---------|-----|------|
| id | bigint | klucz główny |
| session_id | uuid | powiązanie z sesją |
| prompt_name | text | nazwa promptu |
| prompt | text | treść promptu |
| created_at | timestampz | czas zapisu |

### Qdrant - kolekcje wektorowe
- **`yllia_chat_bot`** - statyczna baza wiedzy (FAQ)
- **`yllia_dynamic_qna`** - dynamiczne dane administracyjne
- **Model embeddingów**: `text-embedding-3-large` (3072 wymiary)
- **Metryka**: Cosine similarity

---

## 🚀 Stack technologiczny

### Core Technologies
- **Frontend**: Streamlit 1.48.1 (interfejs czatu)
- **LLM**: OpenAI GPT-4o-mini (generowanie odpowiedzi)
- **Embeddings**: OpenAI text-embedding-3-large (wyszukiwanie semantyczne)
- **Vector DB**: Qdrant (przechowywanie embeddingów)
- **Database**: Supabase (PostgreSQL - sesje, wiadomości, feedback)
- **Observability**: Langfuse (monitoring, traces, feedback)

### Supporting Libraries
- **tiktoken** - liczenie tokenów OpenAI
- **python-dotenv** - zarządzanie zmiennymi środowiskowymi
- **PIL (Pillow)** - obsługa obrazków (awatar)
- **uuid** - generowanie identyfikatorów sesji

### Konfiguracja środowiskowa
```env
# OpenAI
OPENAI_API_KEY=sk-...

# Supabase
SUPABASE_URL=https://...
SUPABASE_SECRET_KEY=...

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=...

# Langfuse
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_ENABLED=true
```

---

## 📊 Kluczowe metryki

### Tokeny i koszty
- **Model główny**: `gpt-4o-mini` ($0.15/$0.60 za M tokenów)
- **Embeddingi**: `text-embedding-3-large`
- **Kurs**: 1 USD = 3.63 PLN (w stałych)
- **Śledzenie**: Precyzyjne liczenie input/output tokenów

### Limity sesji
- **Maksymalnie**: 7 pytań na sesję
- **Powód**: Kontrola kosztów i jakości doświadczenia
- **Reset**: Automatyczny po ocenie końcowej

### Feedback system
- **Per odpowiedź**: 👍/👎 z zapisem do Supabase i Langfuse
- **Per sesja**: Ocena 1-5 + opcjonalny komentarz
- **Analityka**: Pełne śledzenie w Langfuse traces

---

## 🔧 Uruchomienie

### Wymagania
1. Python 3.8+
2. Klucze API: OpenAI, Supabase, Langfuse
3. Instancja Qdrant (lokalnie lub cloud)
4. Plik `.env` z konfiguracją

### Instalacja
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Struktura promptów
- **Główny prompt** (`prompt_general.md`) - pełna rola i instrukcje dla Yllii
- **Streszczenia** (`prompt_summary.md`) - kompresja historii rozmowy  
- **Notatki pacjenta** (`prompt_patients_summary.md`) - czytelne podsumowania

---

## 📞 Kontakt i wsparcie

**Autor**: Damian Siwicki  
**Email**: poczta@siwicki.info  
**Website**: https://damiansiwicki.pl

**Uwaga**: Aplikacja jest w wersji testowej. Yllia nie zastępuje konsultacji medycznej i służy wyłącznie celom informacyjnym dotyczącym organizacji pracy gabinetu psychiatrycznego.

