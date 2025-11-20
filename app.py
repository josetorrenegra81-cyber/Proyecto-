from flask import Flask, request
import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder
import asyncio
import os

# Importa tu bot
import bot

TOKEN = bot.TOKEN

# Crear aplicación de Telegram
app_telegram = ApplicationBuilder().token(TOKEN).build()

# Registrar handlers
app_telegram.add_handler(bot.CommandHandler("start", bot.start))
app_telegram.add_handler(bot.CommandHandler("help", bot.help_command))
app_telegram.add_handler(bot.CommandHandler("evaluar", bot.evaluar_command))
app_telegram.add_handler(bot.CommandHandler("calcular", bot.calcular_porcentaje_command))
app_telegram.add_handler(bot.CommandHandler("estado", bot.estado_command))
app_telegram.add_handler(bot.CommandHandler("programar", bot.programar_evaluaciones_command))
app_telegram.add_handler(bot.MessageHandler(bot.filters.TEXT & ~bot.filters.COMMAND, bot.info_handler))

# Inicializar base de datos
bot.init_db()

# Inicializar la app de Telegram manualmente (importante)
async def init_telegram():
    await app_telegram.initialize()
    await app_telegram.start()
    print("Telegram bot inicializado correctamente.")

asyncio.get_event_loop().run_until_complete(init_telegram())

# Flask server
server = Flask(__name__)

@server.post("/")
def webhook():
    try:
        json_update = request.get_json()
        update = Update.de_json(json_update, app_telegram.bot)

        # Crear tarea asincrónica sin bloquear Flask
        asyncio.create_task(app_telegram.process_update(update))

    except Exception as e:
        print("Error en webhook:", e)

    return "OK", 200

@server.get("/")
def home():
    return "Bot funcionando correctamente 🔥", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
