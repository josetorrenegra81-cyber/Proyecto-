from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder
import asyncio
import os

import bot  # tu bot.py

TOKEN = bot.TOKEN

bot.init_db()

# Construir la app de Telegram
app_telegram = ApplicationBuilder().token(TOKEN).build()

# REGISTRAR HANDLERS
from telegram.ext import CommandHandler, MessageHandler, filters

app_telegram.add_handler(CommandHandler("start", bot.start))
app_telegram.add_handler(CommandHandler("help", bot.help_command))
app_telegram.add_handler(CommandHandler("evaluar", bot.evaluar_command))
app_telegram.add_handler(CommandHandler("calcular", bot.calcular_porcentaje_command))
app_telegram.add_handler(CommandHandler("estado", bot.estado_command))
app_telegram.add_handler(CommandHandler("programar", bot.programar_evaluaciones_command))
app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.info_handler))


# FLASK SERVER
server = Flask(__name__)

@server.post("/")
def webhook():
    update = Update.de_json(request.get_json(), app_telegram.bot)
    asyncio.run(app_telegram.process_update(update))
    return "OK", 200

@server.get("/")
def home():
    return "Bot funcionando correctamente 🔥", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
