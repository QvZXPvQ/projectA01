# ProjectBot — Bot Telegram do Zarządzania Projektami

Bot działa 24/7, jest darmowy i nie wymaga karty kredytowej.

## Struktura plików

```
projectbot/
├── bot.py           ← główny kod bota
├── database.py      ← obsługa bazy danych SQLite
├── ai_helper.py     ← integracja z Groq AI
├── requirements.txt ← biblioteki Python
├── Procfile         ← konfiguracja dla Koyeb
└── README.md        ← ten plik
```

## Zmienne środowiskowe (ustaw w Render)

```
TELEGRAM_TOKEN = token od @BotFather
GROQ_API_KEY   = klucz z console.groq.com
```

## Wdrożenie na Render (darmowe, bez karty kredytowej)

1. Wejdź na render.com → zarejestruj się przez GitHub
2. Kliknij **New +** → **Web Service**
3. Wybierz repozytorium `projectbot`
4. Ustawienia builda:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot.py`
5. Dodaj zmienne środowiskowe (Environment): `TELEGRAM_TOKEN`, `GROQ_API_KEY`
6. Plan: **Free**
7. Kliknij **Create Web Service**

Bot zawiera mini-serwer HTTP (wbudowany w bot.py), dzięki czemu Render
rozpoznaje go jako "Web Service" i hostuje za darmo — bez tego Render
wymagałby płatnego planu "Background Worker".

Pamiętaj o Uptime Robot — Render usypia darmowe serwisy po 15 min
bezczynności, więc monitor pingujący co 5 minut jest konieczny.

## Komendy bota

| Komenda | Opis |
|---|---|
| /start | Powitanie i lista komend |
| /newproject [nazwa] | Utwórz nowy projekt |
| /projects | Lista Twoich projektów |
| /addtask [id] [zadanie] | Dodaj zadanie |
| /tasks | Lista wszystkich zadań |
| /today | Plan na dziś |
| /overdue | Przeterminowane zadania |
| /done [id] | Oznacz zadanie jako gotowe |
| /suggest | AI sugeruje priorytety |
| /ask [pytanie] | Zapytaj AI o projekt |

## Naturaly język

Możesz też pisać naturalnie:
- "Dodaj zadanie: napisać raport, deadline jutro, priorytet wysoki"
- "Co mam dziś do zrobienia?"
- "Pokaż moje zadania"

## Uruchomienie lokalne (do testów)

```bash
pip install -r requirements.txt
export TELEGRAM_TOKEN="twój_token"
export GROQ_API_KEY="twój_klucz"
python bot.py
```
