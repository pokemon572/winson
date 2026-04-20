import os
import discord
from discord.ext import commands
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Lee variables de entorno
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
GOOGLE_CREDENTIALS = os.environ["GOOGLE_CREDENTIALS"]

# Carga credenciales de Google
creds_info = json.loads(GOOGLE_CREDENTIALS)
creds = service_account.Credentials.from_service_account_info(creds_info)
calendar_service = build('calendar', 'v3', credentials=creds)

# Configuración del bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="", intents=intents)  # sin prefijo

# Función de ejemplo para procesar mensajes (puedes conectar Ollama aquí)
def procesar_mensaje(texto):
    # Aquí iría tu lógica de IA o integración con Ollama
    return f"Recibí tu mensaje: {texto}"

# Evento: Winston responde a cualquier mensaje
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Simula que Winston está escribiendo ("pensando...")
    async with message.channel.typing():
        respuesta = procesar_mensaje(message.content)

    await message.channel.send(respuesta)

# Ejemplo de comando para crear eventos en Google Calendar
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
bot.run(DISCORD_TOKEN)

