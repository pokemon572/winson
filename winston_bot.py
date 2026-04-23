def procesar_mensaje(texto: str) -> str:
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",  # modelo activo y soportado
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
