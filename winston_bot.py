import os
import discord
from discord.ext import commands
import json
import requests
import dateparser
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

# Historial de conversación
conversation_history = []

# Función que conecta con Groq
def procesar_mensaje(texto: str) -> str:
    try:
        conversation_history.append({"role": "user", "content": texto})

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",  # modelo activo
                "messages": [
                    {"role": "system", "content": "Eres Winston, un asistente personal claro y estratégico."}
                ] + conversation_history,
                "max_tokens": 15000,
                "temperature": 0.7
            },
            timeout=60
        )

        data = response.json()
        if "choices" in data and len(data["choices"]) > 0:
            respuesta = data["choices"][0]["message"]["content"].strip()
            conversation_history.append({"role": "assistant", "content": respuesta})
            return respuesta
        elif "error" in data:
            return f"Error de Groq: {data['error'].get('message','desconocido')}"
        else:
            return "No recibí respuesta válida de Groq."
    except Exception as e:
        return f"Error al consultar Groq: {e}"

# Evento: Winston responde a cualquier mensaje
@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    async with message.channel.typing():
        respuesta = procesar_mensaje(message.content)
    if not respuesta:
        respuesta = "Lo siento, tuve un problema al procesar tu mensaje."
    await message.channel.send(respuesta)
    await bot.process_commands(message)

# Comando: crear evento en tu calendario personal
@bot.command(name="evento")
async def crear_evento(ctx, titulo: str, inicio: str, fin: str = None):
    inicio_dt = dateparser.parse(inicio)
    fin_dt = dateparser.parse(fin) if fin else None

    if not inicio_dt:
        await ctx.send("No pude entender la fecha/hora que me diste.")
        return

    evento = {
        'summary': titulo,
        'start': {
            'dateTime': inicio_dt.isoformat(),
            'timeZone': 'America/Bogota'
        },
        'end': {
            'dateTime': fin_dt.isoformat() if fin_dt else inicio_dt.isoformat(),
            'timeZone': 'America/Bogota'
        }
    }
    calendar_service.events().insert(
        calendarId='juanse.caballero.r@gmail.com',
        body=evento
    ).execute()
    await ctx.send(f"Evento '{titulo}' creado en tu Google Calendar ✅")

# Comando: listar próximos eventos
@bot.command(name="listar_eventos")
async def listar_eventos(ctx):
    try:
        eventos = calendar_service.events().list(
            calendarId='juanse.caballero.r@gmail.com',
            maxResults=5,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        items = eventos.get('items', [])
        if not items:
            await ctx.send("No encontré eventos próximos en tu calendario.")
        else:
            respuesta = "📅 Próximos eventos:\n"
            for ev in items:
                inicio = ev['start'].get('dateTime', ev['start'].get('date'))
                respuesta += f"- {ev['summary']} (Inicio: {inicio})\n"
            await ctx.send(respuesta)
    except Exception as e:
        await ctx.send(f"Error al acceder al calendario: {e}")

# Arranca el bot
if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("❌ ERROR: La variable DISCORD_TOKEN no está configurada en Railway.")
