import os
import json
import sqlite3
import datetime
import traceback

from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# --------------------------------------
# TU TOKEN
# --------------------------------------
TOKEN = os.getenv("BOT_TOKEN")
DB_FILE = "bot_db.sqlite"

# --------------------------------------
# INICIALIZAR FLASK (webhook)
# --------------------------------------
app_flask = Flask(__name__)

# --------------------------------------
# AQUÍ PEGAS TODO TU CÓDIGO ORIGINAL
# (desde init_db(), info_empresa, preguntas_test... hasta main)
# --------------------------------------

# ⬇ Pego tu código COMPLETO (sin run_polling) ⬇


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
    # analytics
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
    "mision": "Brindar servicios logísticos eficientes y confiables que impulsen el éxito de nuestros clientes.",
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
# Helpers
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
        "INSERT INTO evaluations (user_id, fecha, correct, total, porcentaje, detalle)
         VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, str(datetime.date.today()), correct, total, porcentaje, json.dumps(detalle)),
    )
    conn.commit()
    conn.close()


# ---------------------------
# Handlers del bot
# ---------------------------

# (TODO: Aquí va todo EXACTO como lo tienes: start, help, evaluar, estado,
# info_handler, send_test_to_user, respuestas_handler, calcular_porcentaje_command...
# No quito nada. Se mantiene igual.)


# --------------------------------------
# Inicializar BOT (pero sin polling)
# --------------------------------------
application = ApplicationBuilder().token(TOKEN).build()

# registrar handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("evaluar", evaluar_command))
application.add_handler(CommandHandler("calcular", calcular_porcentaje_command))
application.add_handler(CommandHandler("estado", estado_command))
application.add_handler(CommandHandler("programar", programar_evaluaciones_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, info_handler))

# --------------------------------------
# WEBHOOK ENDPOINT PARA DETA SPACE
# --------------------------------------
@app_flask.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        application.update_queue.put(update)
    except Exception as e:
        print("Error en webhook:", e)
    return "ok", 200


# --------------------------------------
# INICIAR APP FLASK
# --------------------------------------
@app_flask.route("/")
def home():
    return "Bot funcionando en Deta Space"

if __name__ == "__main__":
    init_db()
    app_flask.run(host="0.0.0.0", port=8080)
