from flask import Flask, request
import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder
import asyncio
import os

# Importamos tu bot completo
import bot

TOKEN = bot.TOKEN

# Creamos la app del bot de Telegram
app_telegram = ApplicationBuilder().token(TOKEN).build()

# Registramos handlers
app_telegram.add_handler(bot.CommandHandler("start", bot.start))
app_telegram.add_handler(bot.CommandHandler("help", bot.help_command))
app_telegram.add_handler(bot.CommandHandler("evaluar", bot.evaluar_command))
app_telegram.add_handler(bot.CommandHandler("calcular", bot.calcular_porcentaje_command))
app_telegram.add_handler(bot.CommandHandler("estado", bot.estado_command))
app_telegram.add_handler(bot.CommandHandler("programar", bot.programar_evaluaciones_command))
app_telegram.add_handler(bot.MessageHandler(bot.filters.TEXT & ~bot.filters.COMMAND, bot.info_handler))

# Base de datos
bot.init_db()

# Flask server
app = Flask(__name__)   # ← ← ← IMPORTANTE: ahora se llama "app"

@app.post("/")
def webhook():
    try:
        json_update = request.get_json()
        update = Update.de_json(json_update, app_telegram.bot)
        asyncio.run(app_telegram.process_update(update))
    except Exception as e:
        print("Error en webhook:", e)
    return "OK", 200

@app.get("/")
def home():
    return "Bot funcionando correctamente 🔥", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
