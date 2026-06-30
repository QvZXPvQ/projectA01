# ProjectBot — Bot Telegram do Zarządzania Projektami

## Struktura plików

```
projectbot/
├── bot.py           
├── database.py      
├── ai_helper.py     
├── requirements.txt 
├── Procfile        
└── README.md        
```

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
