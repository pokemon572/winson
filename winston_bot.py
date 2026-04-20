import discord
from discord.ext import commands
import requests
import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ==============================
# CONFIG
# ==============================

MODEL = "winston"
MAX_HISTORY = 6

# Token de Discord desde variable de entorno
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]

# Credenciales de Google Calendar desde variable de entorno
creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
creds = service_account.Credentials.from_service_account_info(creds_info)
calendar_service = build('calendar', 'v3', credentials=creds)

user_histories = {}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==============================
# IA (Ollama)
# ==============================

def consultar_ollama(user_id, pregunta):
    if user_id not in user_histories:
        user_histories[user_id] = []

    history = user_histories[user_id]
    history.append({"role": "user", "content": pregunta})

    if len(history) > MAX_HISTORY:
        history.pop(0)

    prompt = "\n".join([f"{m['role']}: {m['content']}" for m in history])

    url = "http://localhost:11434/api/generate"
    payload = {"model": MODEL, "prompt": prompt, "options": {"num_predict": 300}}
    response = requests.post(url, json=payload, stream=True)

    respuesta = ""
    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode("utf-8"))
            if "response" in data:
                respuesta += data["response"]

    history.append({"role": "assistant", "content": respuesta})
    return respuesta

# ==============================
# Google Calendar
# ==============================

def crear_evento(titulo, inicio, fin):
    event = {
        'summary': titulo,
        'start': {'dateTime': inicio},
        'end': {'dateTime': fin}
    }
    calendar_service.events().insert(calendarId='primary', body=event).execute()

# ==============================
# BOT
# ==============================

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    await bot.tree.sync()

@bot.command()
async def winston(ctx, *, pregunta: str):
    respuesta = consultar_ollama(ctx.author.id, pregunta)
    for i in range(0, len(respuesta), 2000):
        await ctx.author.send(respuesta[i:i+2000])

@bot.command()
async def evento(ctx, titulo: str, inicio: str, fin: str):
    # Ejemplo: !evento "Reunión" "2026-04-20T09:00:00" "2026-04-20T10:00:00"
    crear_evento(titulo, inicio, fin)
    await ctx.send("Evento creado en tu Google Calendar ✅")

bot.run(DISCORD_TOKEN, reconnect=True)
