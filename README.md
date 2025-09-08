# 🌸 Yllia – wirtualna asystentka gabinetu psychiatrycznego

Yllia to cyfrowa asystentka gabinetu psychiatrycznego.  
Odpowiada pacjentom na pytania dotyczące gabinetu, łącząc kontekst statyczny (FAQ) i dynamiczny (np. godziny, urlopy).  
Działa w oparciu o modele OpenAI, bazę wektorową Qdrant, bazę Supabase i system obserwowalności Langfuse.  

---

## ✨ Główne zasady
- **Profesjonalizm i empatia** – Yllia zawsze odpowiada ciepło, jasno i kompletnie.
- **Źródła informacji**:
  - **Kontekst dynamiczny** (np. godziny, urlopy, ceny) – priorytet.
  - **Kontekst statyczny** (FAQ, najczęstsze pytania pacjentów).
- **Bezpieczeństwo** – w sytuacjach kryzysowych kieruje na 112 lub do szpitala psychiatrycznego.
- **Zakres** – odpowiada wyłącznie na pytania związane z gabinetem.

---

## 🏗️ Architektura projektu

### 🔄 Przepływ danych
1. **Użytkownik** wpisuje pytanie w aplikacji Streamlit.
2. **Supabase** – zapis pytania w tabeli `messages` (powiązanej z `sessions`).
3. **Qdrant** – generowanie embeddingu pytania i wyszukiwanie podobnych w:
   - kolekcji `yllia_static` (FAQ),
   - kolekcji `yllia_dynamic` (dane bieżące).
4. **Prompts** – budowa pełnego promptu (`prompt_general.md`) z kontekstem.
5. **OpenAI** – generowanie odpowiedzi.
6. **Supabase** – zapis odpowiedzi w `messages`.
7. **Langfuse** – logowanie całej interakcji.
8. **Streamlit** – wyświetlenie odpowiedzi użytkownikowi.

---

## 📂 Struktura katalogów

yllia_app/
│── app.py # główny plik aplikacji (Streamlit)
│
├── config/ # konfiguracja
│ ├── config.py # klucze i ustawienia środowiskowe (.env)
│ └── constants.py # stałe globalne (role, limity, nazwy tabel, kolekcje)
│
├── services/ # logika komunikacji z zewnętrznymi usługami
│ ├── openai_service.py # komunikacja z OpenAI
│ ├── langfuse_service.py # komunikacja z Langfuse
│ ├── supabase_service.py # komunikacja z Supabase
│ └── qdrant_service.py # komunikacja z Qdrant
│
├── utils/ # funkcje pomocnicze
│ ├── embeddings.py # generowanie embeddingów
│ ├── prompts.py # ładowanie promptów i podstawianie kontekstów
│ └── history.py # skracanie i streszczanie kontekstu rozmowy
│
├── prompts/ # pliki promptów w formacie Markdown
│ ├── prompt_general.md # główna rola Yllii (odpowiedzi dla pacjentów)
│ ├── prompt_summary.md # streszczanie historii rozmów
│ └── prompt_embeddings.md # przygotowanie odpowiedzi do embeddingów
│
└── data/ # dane statyczne/dynamiczne (JSON, CSV itp.)

---
- yllia_app/
  - app.py
  - config/
    - config.py
    - constants.py
  - services/
    - openai_service.py
    - langfuse_service.py
    - supabase_service.py
    - qdrant_service.py
  - utils/
    - embeddings.py
    - prompts.py
    - history.py
  - prompts/
    - prompt_general.md
    - prompt_summary.md
    - prompt_embeddings.md
  - data/

---

## 🗄️ Struktura bazy Supabase

### Tabela `sessions`
| Kolumna      | Typ        | Opis |
|--------------|------------|------|
| id           | UUID (PK)  | unikalny identyfikator sesji |
| created_at   | timestampz | start sesji |
| ended_at     | timestampz | koniec sesji (opcjonalnie) |
| user_agent   | text       | dane o urządzeniu (opcjonalnie) |
| meta         | jsonb      | dodatkowe dane |

### Tabela `messages`
| Kolumna      | Typ        | Opis |
|--------------|------------|------|
| id           | bigserial  | klucz główny |
| session_id   | UUID (FK)  | powiązanie do `sessions` |
| created_at   | timestampz | czas wysłania |
| role         | text       | `user` lub `assistant` |
| content      | text       | treść wiadomości |
| summary      | text       | streszczenie (opcjonalnie) |
| meta         | jsonb      | dodatkowe dane (np. feedback) |

### Tabela `feedback` (opcjonalna)
| Kolumna      | Typ        | Opis |
|--------------|------------|------|
| id           | bigserial  | klucz główny |
| message_id   | bigint (FK)| powiązanie do `messages` |
| rating       | smallint   | ocena (-1 / 0 / +1) |
| comment      | text       | komentarz użytkownika |
| created_at   | timestampz | czas dodania |

---

## 🚀 Technologie

- **Frontend**: Streamlit (chat UI)  
- **LLM**: OpenAI GPT (domyślnie `gpt-4o-mini`)  
- **Vector DB**: Qdrant (kolekcje: `yllia_static`, `yllia_dynamic`)  
- **Relacyjna DB**: Supabase (tabele: `sessions`, `messages`, `feedback`)  
- **Observability**: Langfuse (śledzenie i feedback interakcji)  

---

## 📌 TODO / rozwój
- [ ] Dodać generowanie streszczeń historii do `utils/history.py`
- [ ] Rozbudować feedback użytkowników w Supabase
- [ ] Przygotować panel admina do edycji kontekstu dynamicznego
- [ ] Deploy aplikacji na Streamlit Cloud / własny serwer

---
