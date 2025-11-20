# bot.py - Bot Telegram completo: knowledge base + evaluaciones cada 6 días + estado
from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import sqlite3
import datetime
import json
import traceback

TOKEN = "8202817343:AAHys04UEPVJEJ1f_Os04v8v3_hwG8iNqcU"
DB_FILE = "bot_db.sqlite"

# ---------------------------
# Inicializar DB
# ---------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # users
    c.execute(
        """CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        nombre TEXT,
        username TEXT,
        idioma TEXT DEFAULT 'es',
        fecha_registro TEXT DEFAULT (datetime('now'))
    )"""
    )
    # user_activity
    c.execute(
        """CREATE TABLE IF NOT EXISTS user_activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        mensaje TEXT,
        respuesta_bot TEXT,
        fecha TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )"""
    )
    # evaluations
    c.execute(
        """CREATE TABLE IF NOT EXISTS evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        fecha TEXT,
        correct INTEGER,
        total INTEGER,
        porcentaje INTEGER,
        detalle TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )"""
    )
    # analytics (respuestas temporales)
    c.execute(
        """CREATE TABLE IF NOT EXISTS analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        evento TEXT,
        valor TEXT,
        fecha TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )"""
    )
    # system_logs
    c.execute(
        """CREATE TABLE IF NOT EXISTS system_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        mensaje TEXT,
        fecha TEXT DEFAULT (datetime('now'))
    )"""
    )
    conn.commit()
    conn.close()


# ---------------------------
# Base de conocimiento
# ---------------------------
info_empresa = {
    "que_hace": "La empresa se dedica a proveer soluciones logísticas integrales, transporte y distribución.",
    "productos": "Servicios de transporte, almacenamiento, gestión aduanera y distribución.",
    "servicios": "Transporte nacional, almacenamiento, cross-docking, gestión aduanera.",
    "mision": "Brindar servicios logísticos eficientes y confiables.",
    "vision": "Ser la empresa líder regional en soluciones logísticas para 2030.",
    "valores": "Responsabilidad, compromiso, integridad, calidad y trabajo en equipo.",
    "procesos": "Atención al cliente → Recepción → Almacenaje → Picking → Despacho → Entrega."
}

# ---------------------------
# Preguntas del test
# ---------------------------
preguntas_test = [
    {
        "p": "¿A qué se dedica la empresa?",
        "op": ["Soluciones logísticas integrales", "Fabricación de alimentos", "Servicios financieros"],
        "ans": 0,
    },
    {
        "p": "¿Cuál es uno de nuestros servicios principales?",
        "op": ["Transporte nacional", "Consultoría legal", "Diseño gráfico"],
        "ans": 0,
    },
    {
        "p": "¿Cuál es uno de nuestros valores?",
        "op": ["Impunidad", "Responsabilidad", "Anarquía"],
        "ans": 1,
    },
]


# ---------------------------
# Helpers DB
# ---------------------------
def db_conn():
    return sqlite3.connect(DB_FILE)

def log_system(tipo, mensaje):
    try:
        conn = db_conn()
        c = conn.cursor()
        c.execute("INSERT INTO system_logs (tipo, mensaje) VALUES (?, ?)", (tipo, mensaje))
        conn.commit()
        conn.close()
    except:
        print("Error guardando log")
        print(traceback.format_exc())

def get_or_create_user_by_tg(tg_id, fullname="", username=""):
    conn = db_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE telegram_id = ?", (tg_id,))
    row = c.fetchone()
    if row:
        user_id = row[0]
    else:
        c.execute(
            "INSERT INTO users (telegram_id, nombre, username) VALUES (?, ?, ?)",
            (tg_id, fullname, username),
        )
        conn.commit()
        user_id = c.lastrowid
    conn.close()
    return user_id

def log_activity(user_id, mensaje, respuesta_bot=""):
    conn = db_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO user_activity (user_id, mensaje, respuesta_bot) VALUES (?, ?, ?)",
        (user_id, mensaje, respuesta_bot),
    )
    conn.commit()
    conn.close()

def save_evaluation(user_id, correct, total, porcentaje, detalle):
    conn = db_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO evaluations (user_id, fecha, correct, total, porcentaje, detalle) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, str(datetime.date.today()), correct, total, porcentaje, json.dumps(detalle)),
    )
    conn.commit()
    conn.close()


# ---------------------------
# Handlers principales
# ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.message.from_user
    user_id = get_or_create_user_by_tg(tg.id, tg.full_name, tg.username or "")
    texto = (
        "¡Hola! Soy el bot de capacitación.\n\n"
        "Comandos:\n"
        "/evaluar – Test manual\n"
        "/calcular – Calcular tu resultado\n"
        "/estado – Último porcentaje\n"
        "/help – Ayuda\n\n"
        "También puedes preguntar por misión, visión, valores, servicios, etc."
    )
    await update.message.reply_text(texto)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    tg = update.message.from_user
    user_id = get_or_create_user_by_tg(tg.id, tg.full_name, tg.username or "")

    if text.strip().isdigit():
        await respuestas_handler(update, context)
        return

    if "qué hace" in text or "que hace" in text or "dedica" in text:
        r = info_empresa["que_hace"]
    elif "productos" in text or "vende" in text:
        r = info_empresa["productos"]
    elif "servicios" in text:
        r = info_empresa["servicios"]
    elif "mision" in text or "misión" in text:
        r = info_empresa["mision"]
    elif "vision" in text or "visión" in text:
        r = info_empresa["vision"]
    elif "valores" in text:
        r = info_empresa["valores"]
    elif "proceso" in text:
        r = info_empresa["procesos"]
    else:
        r = (
            "No entendí. Puedes preguntar:\n"
            "- ¿Qué hace la empresa?\n"
            "- ¿Productos?\n"
            "- ¿Servicios?\n"
            "- ¿Misión?/¿Visión?/¿Valores?\n"
            "O usa /evaluar para un test."
        )

    log_activity(user_id, update.message.text, r)
    await update.message.reply_text(r)


# ---------------------------
# Test
# ---------------------------
async def send_test_to_user(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    tg_id = job.data.get("telegram_id")

    bot = context.bot
    await bot.send_message(chat_id=tg_id, text="📋 TEST: responde con el número correcto.")

    for idx, q in enumerate(preguntas_test):
        msg = f"Pregunta {idx+1}: {q['p']}\n"
        for i, op in enumerate(q["op"]):
            msg += f"{i+1}. {op}\n"
        await bot.send_message(chat_id=tg_id, text=msg)


async def evaluar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.message.from_user.id
    jq = context.application.job_queue
    jq.run_once(send_test_to_user, when=0, data={"telegram_id": tg_id})
    await update.message.reply_text("Test enviado. Responde con números.")


async def respuestas_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.message.from_user
    user_id = get_or_create_user_by_tg(tg.id, tg.full_name, tg.username or "")
    num = update.message.text.strip()

    conn = db_conn()
    c = conn.cursor()
    c.execute("INSERT INTO analytics (user_id, evento, valor) VALUES (?, ?, ?)", (user_id, "test_answer", num))
    conn.commit()
    conn.close()

    await update.message.reply_text("Respuesta guardada. Cuando termines escribe /calcular")


async def calcular_porcentaje_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.message.from_user
    user_id = get_or_create_user_by_tg(tg.id, tg.full_name, tg.username or "")

    conn = db_conn()
    c = conn.cursor()
    total_p = len(preguntas_test)
    c.execute(
        "SELECT valor FROM analytics WHERE user_id = ? AND evento = 'test_answer' ORDER BY id DESC LIMIT ?",
        (user_id, total_p),
    )
    rows = c.fetchall()
    conn.close()

    rows = list(reversed(rows))
    respuestas = [int(r[0]) for r in rows]

    correct = 0
    detalle = []
    for i, q in enumerate(preguntas_test):
        resp = respuestas[i] - 1 if i < len(respuestas) else None
        ok = (resp == q["ans"])
        if ok:
            correct += 1
        detalle.append({"pregunta": q["p"], "resp": resp, "correcta": q["ans"], "ok": ok})

    porcentaje = int((correct / len(preguntas_test)) * 100)
    save_evaluation(user_id, correct, len(preguntas_test), porcentaje, detalle)

    # limpieza
    conn = db_conn()
    c = conn.cursor()
    c.execute("DELETE FROM analytics WHERE user_id = ? AND evento = 'test_answer'", (user_id,))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"📊 Resultado: {porcentaje}%\nCorrectas: {correct}/{len(preguntas_test)}")


async def estado_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.message.from_user
    user_id = get_or_create_user_by_tg(tg.id, tg.full_name, tg.username or "")

    conn = db_conn()
    c = conn.cursor()
    c.execute("SELECT fecha, porcentaje, correct, total FROM evaluations WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        await update.message.reply_text("No tienes evaluaciones. Usa /evaluar")
    else:
        fecha, porc, crr, ttl = row
        await update.message.reply_text(f"Última evaluación ({fecha}):\n📊 {porc}%\nCorrectas {crr}/{ttl}")


async def programar_evaluaciones_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = db_conn()
    c = conn.cursor()
    c.execute("SELECT telegram_id FROM users")
    rows = c.fetchall()
    conn.close()

    jq = context.application.job_queue
    interval = 6 * 24 * 3600  # 6 días

    for r in rows:
        tg_id = r[0]
        jq.run_repeating(send_test_to_user, interval=interval, first=0, data={"telegram_id": tg_id})

    await update.message.reply_text(f"Evaluaciones automáticas programadas para {len(rows)} usuarios.") 
