from dotenv import load_dotenv
import os
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configurar Dialogflow
dialogflow_project_id = os.getenv("DIALOGFLOW_PROJECT_ID")
dialogflow_session_id = "meu_bot_sessao"
dialogflow_language_code = "es"