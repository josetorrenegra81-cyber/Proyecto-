from flask import Flask, request
import asyncio
import os

from telegram import Update
from telegram.ext import ApplicationBuilder
import bot

TOKEN = bot.TOKEN

# Crear app Flask
server = Flask(__name__)

# Crear app de Telegram SIN iniciarla aún
app_telegram = ApplicationBuilder().token(TOKEN).build()

# Registrar handlers
app_telegram.add_handler(bot.CommandHandler("start", bot.start))
app_telegram.add_handler(bot.CommandHandler("help", bot.help_command))
app_telegram.add_handler(bot.CommandHandler("evaluar", bot.evaluar_command))
app_telegram.add_handler(bot.CommandHandler("calcular", bot.calcular_porcentaje_command))
app_telegram.add_handler(bot.CommandHandler("estado", bot.estado_command))
app_telegram.add_handler(bot.CommandHandler("programar", bot.programar_evaluaciones_command))
app_telegram.add_handler(bot.MessageHandler(bot.filters.TEXT & ~bot.filters.COMMAND, bot.info_handler))

# Inicializar DB
bot.init_db()

# Iniciar Telegram bot dentro del loop correcto
initialized = False

async def init_bot():
    global initialized
    if not initialized:
        await app_telegram.initialize()
        await app_telegram.start()
        initialized = True
        print("🔥 Bot de Telegram inicializado correctamente 🔥")


@server.post("/")
def webhook():
    json_data = request.get_json()

    asyncio.get_event_loop().create_task(process_update_async(json_data))

    return "OK", 200


async def process_update_async(json_data):
    await init_bot()  # Inicializa solo una vez

    update = Update.de_json(json_data, app_telegram.bot)
    await app_telegram.process_update(update)


@server.get("/")
def home():
    return "Bot funcionando correctamente en Render 😎", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
