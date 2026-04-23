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

# Credenciales de Google
creds_info = json.loads(GOOGLE_CREDENTIALS)
creds = service_account.Credentials.from_service_account_info(creds_info)
calendar_service = build('calendar', 'v3', credentials=creds)

# Configuración del bot con intents completos
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="", intents=intents)

# Función que conecta con Ollama
def procesar_mensaje(texto: str) -> str:
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3", "prompt": texto},
            timeout=60
        )
        # Ollama devuelve varias líneas JSON, tomamos la última
        output = ""
        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                if "response" in data:
                    output += data["response"]
        return output.strip() if output else "No pude generar respuesta."
    except Exception as e:
        return f"Error al consultar Ollama: {e}"

# Evento: Winston responde a cualquier mensaje
@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    # Simula que Winston está escribiendo ("pensando...")
    async with message.channel.typing():
        respuesta = procesar_mensaje(message.content)

    await message.channel.send(respuesta)

    # Mantiene los comandos funcionando
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
