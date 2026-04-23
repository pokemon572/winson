import os
import discord
from discord.ext import commands
import json
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Variables de entorno
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GOOGLE_CREDENTIALS = os.environ.get("GOOGLE_CREDENTIALS")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Credenciales de Google
creds_info = json.loads(GOOGLE_CREDENTIALS)
creds = service_account.Credentials.from_service_account_info(creds_info)
calendar_service = build('calendar', 'v3', credentials=creds)

# Configuración del bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="", intents=intents)

# Función que conecta con Groq
def procesar_mensaje(texto: str) -> str:
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.2-3b-preview",  # modelo activo y recomendado
                "messages": [
                    {"role": "system", "content": "Eres Winston, un asistente personal claro y estratégico."},
                    {"role": "user", "content": texto}
                ],
                "max_tokens": 300,
                "temperature": 0.7
            },
            timeout=60
        )
        data = response.json()
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"].strip()
        elif "error" in data:
            return f"Error de Groq: {data['error'].get('message','desconocido')}"
        else:
            return f"Respuesta inesperada de Groq: {data}"
    except Exception as e:
        return f"Error al consultar Groq: {e}"

# Evento: Winston responde a cualquier mensaje
@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    async with message.channel.typing():
        respuesta = procesar_mensaje(message.content)

    await message.channel.send(respuesta)
    await bot.process_commands(message)

# Comando para crear eventos en Google Calendar
@bot.command(name="evento")
async def crear_evento(ctx, titulo: str, inicio: str, fin: str):
    evento = {
        'summary': titulo,
        'start': {'dateTime': inicio},
        'end': {'dateTime': fin}
    }
    calendar_service.events().insert(calendarId='primary', body=evento).execute()
    await ctx.send(f"Evento '{titulo}' creado en tu Google Calendar ✅")

# Arranca el bot
if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("❌ ERROR: La variable DISCORD_TOKEN no está configurada en Railway.")
