# 🤖 pp_bot_telegram conectado a ChatGPT

Este es un bot de Telegram que utiliza el modelo de lenguaje de ChatGPT para generar respuestas a los mensajes de los usuarios.

## 🖥️ Instalación

1. Clona este repositorio
2. Instala las dependencias con `pip install -r requirements.txt`
3. Ejecuta el bot con `python bot.py`
4. Crea un proyecto en google cloud. https://console.cloud.google.com/
5. Crear un archivo .env en la raiz del proyecto, con la siguiente información:
   - OPENAI_API_KEY=tu_key
   - TELEGRAM_TOKEN=tu_token_telegram
   - GOOGLE_APPLICATION_CREDENTIALS=tus_credenciales_dialogflow
   - DIALOGFLOW_PROJECT_ID=id_proyecto
