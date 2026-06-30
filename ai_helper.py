import os
import json
import urllib.request
import urllib.error

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def ask_ai(system_prompt, user_message):
    """Wysyła zapytanie do Groq AI i zwraca odpowiedź."""
    if not GROQ_API_KEY:
        return "Brak klucza GROQ_API_KEY. Sprawdź zmienne środowiskowe."

    payload = json.dumps({
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }).encode("utf-8")

    req = urllib.request.Request(
        GROQ_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        return f"Błąd API: {e.code}"
    except Exception as e:
        return f"Błąd połączenia: {str(e)}"


def parse_task_from_text(text):
    """Używa AI do wyciągnięcia zadania z naturalnego języka."""
    system = """Jesteś asystentem który wyciąga informacje o zadaniu z tekstu.
Zwróć TYLKO JSON w formacie:
{"title": "nazwa zadania", "deadline": "YYYY-MM-DD lub null", "priority": "low/medium/high/critical"}

Priorytety: pilne/critical/krytyczne=critical, wysoki/ważny=high, niski/mało ważny=low, reszta=medium
Daty: dzisiaj, jutro, pojutrze, nazwy dni tygodnia przelicz na format YYYY-MM-DD.
Dzisiaj jest: """ + __import__('datetime').date.today().isoformat()

    result = ask_ai(system, text)

    try:
        start = result.find("{")
        end = result.rfind("}") + 1
        return json.loads(result[start:end])
    except Exception:
        return {"title": text, "deadline": None, "priority": "medium"}


def get_ai_suggestion(tasks_text):
    """Pyta AI o sugestię priorytetów."""
    system = """Jesteś asystentem do zarządzania projektami.
Analizujesz listę zadań i podajesz krótką, konkretną radę co zrobić najpierw i dlaczego.
Odpowiadaj po polsku, maksymalnie 3-4 zdania. Bądź konkretny."""

    return ask_ai(system, f"Oto moje zadania:\n{tasks_text}\n\nCo powinienem zrobić najpierw?")


def ask_about_project(question, context):
    """Odpowiada na dowolne pytanie o projekt."""
    system = """Jesteś pomocnym asystentem do zarządzania projektami.
Odpowiadaj po polsku, konkretnie i krótko (max 5 zdań).
Masz dostęp do kontekstu projektu użytkownika."""

    return ask_ai(system, f"Kontekst:\n{context}\n\nPytanie: {question}")
