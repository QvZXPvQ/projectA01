import os
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)
import database as db
import ai_helper as ai

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = os.getenv("TELEGRAM_TOKEN", "")

PRIORITY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢"
}

STATUS_EMOJI = {
    "todo": "📋",
    "in_progress": "⚙️",
    "done": "✅"
}

# ── POMOCNICZE ────────────────────────────────────────────
def format_task(task):
    p = PRIORITY_EMOJI.get(task["priority"], "⚪")
    s = STATUS_EMOJI.get(task["status"], "❓")
    deadline = f" | 📅 {task['deadline']}" if task["deadline"] else ""
    return f"{s} {p} [{task['id']}] {task['title']}{deadline}"

def get_user_context(user_id):
    projects = db.get_projects(user_id)
    tasks = db.get_todays_tasks()
    ctx = "PROJEKTY:\n"
    for p in projects:
        ctx += f"- [{p['id']}] {p['name']}\n"
    ctx += "\nZADANIA:\n"
    for t in tasks:
        ctx += f"- [{t['id']}] {t['title']} (priorytet: {t['priority']}, deadline: {t['deadline']})\n"
    return ctx

# ── KOMENDY ───────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.save_user(user.id, user.username, user.first_name)

    text = (
        f"👋 Cześć *{user.first_name}*! Jestem Twoim botem do zarządzania projektami.\n\n"
        "📋 *Co umiem:*\n"
        "/newproject — utwórz nowy projekt\n"
        "/projects — lista Twoich projektów\n"
        "/addtask — dodaj zadanie\n"
        "/tasks — lista zadań\n"
        "/today — co dziś do zrobienia\n"
        "/overdue — przeterminowane zadania\n"
        "/done [id] — oznacz zadanie jako gotowe\n"
        "/suggest — AI sugeruje priorytety\n"
        "/ask [pytanie] — zapytaj AI o projekt\n\n"
        "💡 Możesz też pisać naturalnie, np:\n"
        "_'Dodaj zadanie: napisać ofertę, deadline piątek, priorytet wysoki'_"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def new_project(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = ctx.args

    if not args:
        await update.message.reply_text(
            "📌 Podaj nazwę projektu:\n`/newproject Nazwa projektu`",
            parse_mode="Markdown"
        )
        return

    name = " ".join(args)
    project_id = db.create_project(name, user.id)

    await update.message.reply_text(
        f"✅ *Projekt utworzony!*\n\n"
        f"📁 Nazwa: {name}\n"
        f"🆔 ID: `{project_id}`\n\n"
        f"Dodaj pierwsze zadanie: `/addtask {project_id} Nazwa zadania`",
        parse_mode="Markdown"
    )

async def list_projects(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    projects = db.get_projects(user.id)

    if not projects:
        await update.message.reply_text(
            "📂 Nie masz jeszcze żadnych projektów.\n"
            "Utwórz pierwszy: `/newproject Nazwa projektu`",
            parse_mode="Markdown"
        )
        return

    text = "📁 *Twoje projekty:*\n\n"
    for p in projects:
        tasks = db.get_tasks(project_id=p["id"])
        done = sum(1 for t in tasks if t["status"] == "done")
        text += f"[{p['id']}] *{p['name']}*\n"
        text += f"    📋 Zadań: {len(tasks)} | ✅ Gotowych: {done}\n\n"

    await update.message.reply_text(text, parse_mode="Markdown")

async def add_task(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args

    if not args:
        await update.message.reply_text(
            "📝 Użycie:\n`/addtask [id_projektu] Nazwa zadania`\n\n"
            "Lub naturalnie: _'Dodaj zadanie: napisać raport, deadline jutro, priorytet wysoki'_",
            parse_mode="Markdown"
        )
        return

    # Sprawdź czy pierwszy argument to ID projektu
    try:
        project_id = int(args[0])
        title_text = " ".join(args[1:])
    except ValueError:
        # Brak ID — użyj pierwszego aktywnego projektu
        projects = db.get_projects(update.effective_user.id)
        if not projects:
            await update.message.reply_text("❌ Najpierw utwórz projekt: `/newproject Nazwa`", parse_mode="Markdown")
            return
        project_id = projects[0]["id"]
        title_text = " ".join(args)

    # Parsuj przez AI
    await update.message.reply_text("🤖 Analizuję zadanie...", parse_mode="Markdown")
    parsed = ai.parse_task_from_text(title_text)

    task_id = db.create_task(
        project_id=project_id,
        title=parsed["title"],
        deadline=parsed.get("deadline"),
        priority=parsed.get("priority", "medium")
    )

    project = db.get_project(project_id)
    p_emoji = PRIORITY_EMOJI.get(parsed.get("priority", "medium"), "🟡")

    await update.message.reply_text(
        f"✅ *Zadanie dodane!*\n\n"
        f"📌 Projekt: {project['name'] if project else 'nieznany'}\n"
        f"🎯 Zadanie: {parsed['title']}\n"
        f"📅 Deadline: {parsed.get('deadline') or 'nie ustawiony'}\n"
        f"{p_emoji} Priorytet: {parsed.get('priority', 'medium')}\n"
        f"🆔 ID: `{task_id}`\n\n"
        f"Oznacz jako gotowe: `/done {task_id}`",
        parse_mode="Markdown"
    )

async def list_tasks(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    project_id = int(args[0]) if args else None

    tasks = db.get_tasks(project_id=project_id)

    if not tasks:
        await update.message.reply_text("📋 Brak zadań. Dodaj pierwsze: `/addtask`", parse_mode="Markdown")
        return

    text = "📋 *Lista zadań:*\n\n"
    for t in tasks:
        text += format_task(t) + "\n"
        if t["project_name"]:
            text += f"   📁 {t['project_name']}\n"

    await update.message.reply_text(text, parse_mode="Markdown")

async def today(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tasks = db.get_todays_tasks()
    overdue = db.get_overdue_tasks()

    if not tasks:
        await update.message.reply_text("🎉 Brak zadań! Możesz odpocząć 😄")
        return

    text = "📅 *Plan na dziś:*\n\n"

    if overdue:
        text += "⚠️ *PRZETERMINOWANE:*\n"
        for t in overdue:
            text += f"  🔴 [{t['id']}] {t['title']} (było: {t['deadline']})\n"
        text += "\n"

    critical = [t for t in tasks if t["priority"] == "critical"]
    high = [t for t in tasks if t["priority"] == "high"]
    rest = [t for t in tasks if t["priority"] in ("medium", "low")]

    if critical:
        text += "🔴 *KRYTYCZNE:*\n"
        for t in critical:
            text += f"  [{t['id']}] {t['title']}"
            if t["deadline"]:
                text += f" | 📅 {t['deadline']}"
            text += "\n"
        text += "\n"

    if high:
        text += "🟠 *WAŻNE:*\n"
        for t in high:
            text += f"  [{t['id']}] {t['title']}"
            if t["deadline"]:
                text += f" | 📅 {t['deadline']}"
            text += "\n"
        text += "\n"

    if rest:
        text += "🟡 *POZOSTAŁE:*\n"
        for t in rest[:5]:  # max 5
            text += f"  [{t['id']}] {t['title']}\n"
        text += "\n"

    text += "_Oznacz gotowe: /done [id]_"
    await update.message.reply_text(text, parse_mode="Markdown")

async def overdue(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tasks = db.get_overdue_tasks()

    if not tasks:
        await update.message.reply_text("✅ Brak przeterminowanych zadań! Dobra robota!")
        return

    text = "⚠️ *Przeterminowane zadania:*\n\n"
    for t in tasks:
        text += f"🔴 [{t['id']}] {t['title']}\n"
        text += f"   📅 Był deadline: {t['deadline']}\n\n"

    await update.message.reply_text(text, parse_mode="Markdown")

async def done(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Użycie: `/done [id_zadania]`", parse_mode="Markdown")
        return

    try:
        task_id = int(ctx.args[0])
    except ValueError:
        await update.message.reply_text("❌ Podaj prawidłowe ID zadania (liczbę).")
        return

    task = db.get_task(task_id)
    if not task:
        await update.message.reply_text(f"❌ Zadanie #{task_id} nie istnieje.")
        return

    db.update_task_status(task_id, "done")
    await update.message.reply_text(f"✅ Zadanie *{task['title']}* oznaczone jako gotowe! 🎉", parse_mode="Markdown")

async def suggest(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tasks = db.get_todays_tasks()

    if not tasks:
        await update.message.reply_text("📋 Brak zadań do analizy.")
        return

    await update.message.reply_text("🤖 AI analizuje Twoje zadania...")

    tasks_text = "\n".join([
        f"- [{t['id']}] {t['title']} (priorytet: {t['priority']}, deadline: {t['deadline'] or 'brak'})"
        for t in tasks
    ])

    suggestion = ai.get_ai_suggestion(tasks_text)
    await update.message.reply_text(f"💡 *Sugestia AI:*\n\n{suggestion}", parse_mode="Markdown")

async def ask(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Użycie: `/ask Twoje pytanie`", parse_mode="Markdown")
        return

    question = " ".join(ctx.args)
    user = update.effective_user
    context = get_user_context(user.id)

    await update.message.reply_text("🤖 Myślę...")
    answer = ai.ask_about_project(question, context)
    await update.message.reply_text(f"🤖 {answer}")

# ── NATURALNY JĘZYK ───────────────────────────────────────
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    user = update.effective_user

    # Rozpoznaj intencję
    if any(w in text for w in ["dodaj zadanie", "nowe zadanie", "utwórz zadanie", "add task"]):
        projects = db.get_projects(user.id)
        if not projects:
            await update.message.reply_text("❌ Najpierw utwórz projekt: `/newproject Nazwa`", parse_mode="Markdown")
            return

        await update.message.reply_text("🤖 Analizuję zadanie...")
        parsed = ai.parse_task_from_text(update.message.text)
        project_id = projects[0]["id"]
        task_id = db.create_task(project_id, parsed["title"], parsed.get("deadline"), parsed.get("priority", "medium"))

        p_emoji = PRIORITY_EMOJI.get(parsed.get("priority", "medium"), "🟡")
        await update.message.reply_text(
            f"✅ *Zadanie dodane!*\n\n"
            f"🎯 {parsed['title']}\n"
            f"📅 {parsed.get('deadline') or 'brak deadline'}\n"
            f"{p_emoji} Priorytet: {parsed.get('priority', 'medium')}\n"
            f"🆔 ID: `{task_id}`",
            parse_mode="Markdown"
        )

    elif any(w in text for w in ["co dziś", "plan na dziś", "co mam dziś"]):
        await today(update, ctx)

    elif any(w in text for w in ["lista zadań", "moje zadania", "pokaż zadania"]):
        await list_tasks(update, ctx)

    else:
        # Ogólne pytanie do AI
        context = get_user_context(user.id)
        await update.message.reply_text("🤖 Myślę...")
        answer = ai.ask_about_project(update.message.text, context)
        await update.message.reply_text(f"🤖 {answer}")

# ── MINI SERWER HTTP (żeby Render rozpoznał nas jako Web Service) ──
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ProjectBot dziala! Bot jest online.")

    def log_message(self, format, *args):
        pass  # wycisz logi serwera HTTP, zeby nie zasmiecaly konsoli

def run_fake_web_server():
    port = int(os.getenv("PORT", 10000))  # Render sam ustawia zmienna PORT
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    print(f"Mini serwer HTTP dziala na porcie {port} (wymagane przez Render)")
    server.serve_forever()

# ── URUCHOMIENIE ──────────────────────────────────────────
def main():
    if not TOKEN:
        print("BŁĄD: Brak TELEGRAM_TOKEN w zmiennych środowiskowych!")
        return

    # Inicjalizacja bazy danych
    db.create_tables()

    # Uruchom mini serwer HTTP w tle (osobny wątek) — to oszukuje Render
    # że to "Web Service", a nie "Background Worker"
    http_thread = threading.Thread(target=run_fake_web_server, daemon=True)
    http_thread.start()

    # Uruchomienie bota
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newproject", new_project))
    app.add_handler(CommandHandler("projects", list_projects))
    app.add_handler(CommandHandler("addtask", add_task))
    app.add_handler(CommandHandler("tasks", list_tasks))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("overdue", overdue))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("suggest", suggest))
    app.add_handler(CommandHandler("ask", ask))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot uruchomiony!")
    app.run_polling()

if __name__ == "__main__":
    main()
