from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
import unicodedata
import os
import openai
import logging
import dialogflow_v2 as dialogflow

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configurar Dialogflow
dialogflow_project_id = os.getenv("DIALOGFLOW_PROJECT_ID")
dialogflow_session_id = "meu_bot_sessao"
dialogflow_language_code = "es"

# Diccionario para guardar mensajes y nombres de usuarios
usuarios = {}

# Lista de palabras clave relacionadas con pediculosis y parasitismo
palabras_clave = {
    "pediculosis": [
        "pediculosis",
        "piojos",
        "infestación",
        "tratamiento",
        "sintomas",
        "prevención",
        "liendres",
        "pelo",
        "cabeza",
        "cuerpo",
        "ropa",
        "peine",
        "insecticida",
        "lavado",
        "contagio",
        "picaduras",
        "puntitos",
        "picores",
    ],
    "parasitismo": [
        "parasitismo",
        "parásitos",
        "infestación",
        "tratamiento",
        "sintomas",
        "prevención",
        "gusanos",
        "lombrices",
        "tenias",
        "ascaris",
        "anquilostomas",
        "tricocéfalos",
        "oxiuros",
        "amebas",
        "protozoos",
        "helmintos",
        "infección",
        "contagio",
        "diagnóstico",
        "medicamentos",
        "hospedador",
        "hospedero",
        "transmisión",
        "ciclo de vida",
        "huevos",
        "larvas",
        "adultos",
        "parasitosis",
        "parasitología",
        "parasitólogo",
        "parasitaria",
        "parasitarias",
        "parasitario",
        "parasitarios",
    ],
}
palabras_despedida = [
    "adiós",
    "hasta luego",
    "nos vemos",
    "me despido",
    "chao",
    "gracias",
    "bye",
]

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Normalizar el texto acentuado
def normalize_text(text):
    """
    The `normalize_text` function takes a text input, normalizes it by decomposing any accented
    characters into their base form, removes any combining diacritical marks, and converts the text to
    lowercase.

    :param text: The `normalize_text` function takes a text input and normalizes it by decomposing any
    accented characters into their base characters and then removing any combining diacritical marks.
    Finally, it converts the text to lowercase before returning the normalized text
    :return: The `normalize_text` function takes a text input, normalizes it using Unicode normalization
    form NFD, removes any combining diacritical marks, and converts the text to lowercase. The function
    returns the normalized and lowercase text.
    """
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    ).lower()


# Colocar la primera letra mayúscula
def capitalize_first_letter(text):
    """
    The function `capitalize_first_letter` takes a string as input and returns the same string with the
    first letter capitalized.

    :param text: The `capitalize_first_letter` function takes a `text` parameter, which is a string that
    you want to capitalize the first letter of. The function returns the input text with the first
    letter capitalized
    :return: The function `capitalize_first_letter` takes a text input and returns the same text with
    the first letter capitalized.
    """
    return text[0].upper() + text[1:]


# Guardar el mensaje del usuario
def handle_user_message(user_id, message_text):
    """
    The function `handle_user_message` stores user messages in a dictionary based on the user ID.

    :param user_id: The `user_id` parameter is a unique identifier for the user who sent the message. It
    is used to keep track of the user's interactions and messages within the system
    :param message_text: The `message_text` parameter in the `handle_user_message` function is the text
    of the message sent by the user. It is the content of the user's message that will be stored in the
    `usuarios` dictionary under the respective user's ID
    """
    if user_id not in usuarios:
        usuarios[user_id] = {
            "messages": [{"role": "user", "content": message_text}],
            "name": None,
            "tema": None,
        }
    else:
        usuarios[user_id]["messages"].append({"role": "user", "content": message_text})


# Comprobar si el mensaje está relacionado con el tema seleccionado
def mensaje_relacionado_con_temas(message_text, tema):
    """
    This Python function checks if a message contains any keywords related to a specific topic and logs
    the result.

    :param message_text: Please provide the `message_text` that you want to check for related topics
    :param tema: The `tema` parameter is a topic or theme that is being checked for relevance in the
    message text. The function `mensaje_relacionado_con_temas` takes in a message text and a topic, and
    then checks if any keywords related to that topic are present in the message text
    :return: The function `mensaje_relacionado_con_temas` returns a boolean value indicating whether the
    message text is related to the specified topic (`tema`).
    """
    normalized_message = normalize_text(message_text)
    related = any(
        normalize_text(palabra) in normalized_message
        for palabra in palabras_clave.get(tema, [])
    )
    logger.info(f"Mensaje relacionado con tema '{tema}': {related}")
    return related


# Comprobar si el mensaje es una despedida
def mensaje_de_despedida(message_text):
    """
    The function checks if any word in the input message is included in a predefined list of farewell
    words.

    :param message_text: The `mensaje_de_despedida` function takes a `message_text` parameter, which is
    a string representing a message. The function checks if any of the words in the `palabras_despedida`
    list are present in the `message_text` after converting both the message and the words in
    :return: The function `mensaje_de_despedida` is returning a boolean value. It checks if any word in
    the `message_text` (converted to lowercase) is present in the list `palabras_despedida`. If at least
    one word is found, it returns `True`, otherwise it returns `False`.
    """
    return any(palabra in message_text.lower() for palabra in palabras_despedida)


# Enviar el mensaje a Dialogflow y obtener la respuesta
def get_dialogflow_response(message_text):
    """
    The function `get_dialogflow_response` processes a message text using Dialogflow to extract and
    format fulfillment messages with images, titles, and buttons.

    :param message_text: The `get_dialogflow_response` function you provided seems to be a Python
    function that interacts with Dialogflow to get responses based on a given message text. It
    constructs messages based on the fulfillment messages received from Dialogflow
    :return: The `get_dialogflow_response` function returns a list of messages extracted from the
    fulfillment messages received from Dialogflow. These messages can include a combination of text,
    images, and buttons.
    """
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(dialogflow_project_id, dialogflow_session_id)
    text_input = dialogflow.types.TextInput(
        text=message_text, language_code=dialogflow_language_code
    )
    query_input = dialogflow.types.QueryInput(text=text_input)

    response = session_client.detect_intent(session=session, query_input=query_input)

    # Imprimir la respuesta completa para depuración
    logger.info(f"Respuesta completa de Dialogflow: {response}")

    # Lista para almacenar todos los mensajes
    messages = []

    # Iterar sobre cada mensaje de fulfillment
    for fulfillment_message in response.query_result.fulfillment_messages:
        if fulfillment_message.HasField("card"):
            card = fulfillment_message.card
            image_url = card.image_uri
            title = card.title
            buttons = card.buttons

            # Verifica si hay una imagen, un título y botones para crear un mensaje combinado
            if image_url and title and buttons:
                button_list = [
                    InlineKeyboardButton(text=button.text, url=button.postback)
                    for button in buttons
                ]

                # Construir el mensaje combinado
                messages.append(
                    {
                        "type": "combined",
                        "photo": image_url,
                        "text": title,
                        "buttons": button_list,
                    }
                )

    return messages


# Generar la respuesta del bot
def generate_response(user_id):
    """
    The function `generate_response` uses OpenAI's GPT-3.5-turbo model to generate a response based on
    the messages associated with a user ID, and then adds the response to the user's message history.

    :param user_id: The `user_id` parameter in the `generate_response` function is used to identify a
    specific user for whom a response is being generated. This user ID is used to retrieve the messages
    associated with that user from the `usuarios` dictionary, which presumably contains information
    about users and their messages. The response
    :return: The function `generate_response(user_id)` returns the reply generated by the OpenAI
    ChatCompletion model based on the messages associated with the user ID provided as input.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=usuarios[user_id]["messages"],
    )

    # Obtener la respuesta
    reply = response.choices[0].message["content"]

    # Añadir la respuesta al diccionario
    usuarios[user_id]["messages"].append({"role": "assistant", "content": reply})
    return reply


# Comprobar si el mensaje está relacionado con cualquier tema disponible
def mensaje_relacionado_con_otro_tema(message_text, tema_actual):
    """
    This Python function compares a given message with keywords related to different topics to determine
    if the message is related to a different topic than the current one.

    :param message_text: It looks like you have provided the function definition for a function that
    checks if a message is related to another topic based on keywords. However, you have not provided
    the actual message text that needs to be checked. Could you please provide the message text so that
    I can assist you further with this function?
    :param tema_actual: The `tema_actual` parameter represents the current topic or theme you are
    working on or discussing. The function `mensaje_relacionado_con_otro_tema` is designed to analyze a
    message text and determine if it is related to a different topic based on a set of keywords
    associated with various topics
    :return: a different topic (tema) that is related to the message text provided, based on a
    dictionary of keywords associated with different topics. If any of the keywords for a different
    topic are found in the normalized message text and that topic is not the current topic, then that
    different topic is returned. If no such topic is found, it returns None.
    """
    normalized_message = normalize_text(message_text)
    for tema, palabras in palabras_clave.items():
        if tema != tema_actual and any(
            normalize_text(palabra) in normalized_message for palabra in palabras
        ):
            return tema
    return None


# Función que se ejecuta cuando se recibe un mensaje
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        user_id = update.message.from_user.id
        message_text = update.message.text.lower()

        logger.info(f"Mensaje recibido de {user_id}: {message_text}")

        if user_id not in usuarios:
            await update.message.reply_text("Hola🖐️, ¿cómo estás? ¿Cuál es tu nombre?")
            usuarios[user_id] = {"messages": [], "name": None, "tema": None}
        elif usuarios[user_id]["name"] is None:
            usuarios[user_id]["name"] = message_text
            keyboard = [
                [InlineKeyboardButton("Pediculosis", callback_data="pediculosis")],
                [InlineKeyboardButton("Parasitismo", callback_data="parasitismo")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"Hola 🙋‍♂️ {capitalize_first_letter(message_text)}, bienvenido a Pediculosis y Parasitismo Bot🤖. Escoge una de las siguientes opciones:",
                reply_markup=reply_markup,
            )
        elif usuarios[user_id]["tema"] is None:
            await update.message.reply_text(
                "Por favor, selecciona una opción del menú."
            )
        else:
            tema_actual = usuarios[user_id]["tema"]
            if mensaje_relacionado_con_temas(message_text, tema_actual):
                handle_user_message(user_id, message_text)
                response = generate_response(user_id)
                logger.info(f"Respuesta generada para {user_id}: {response}")
                if response:
                    await update.message.reply_text(response)
            else:
                otro_tema = mensaje_relacionado_con_otro_tema(message_text, tema_actual)
                if otro_tema:
                    keyboard = [
                        [
                            InlineKeyboardButton(
                                "Volver a seleccionar tema",
                                callback_data="volver_a_seleccionar",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                f"Seguir con {capitalize_first_letter(tema_actual)}",
                                callback_data="continuar_con_el_mismo",
                            )
                        ],
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(
                        f"Parece que tu pregunta está relacionada con {otro_tema}. "
                        f"Sin embargo, seleccionaste el tema {tema_actual}. "
                        f"Por favor, selecciona el tema correcto o formula una pregunta sobre {tema_actual}.",
                        reply_markup=reply_markup,
                    )
                elif mensaje_de_despedida(message_text):
                    keyboard = [
                        [
                            InlineKeyboardButton(
                                "SI, Terminar", callback_data="confirm_si"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "NO, Continuar", callback_data="confirm_no"
                            )
                        ],
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(
                        "¿Fue clara la información o necesitas algo más?",
                        reply_markup=reply_markup,
                    )
                    usuarios[user_id]["esperando_confirmacion"] = True
                elif usuarios[user_id].get("esperando_confirmacion"):
                    keyboard = [
                        [
                            InlineKeyboardButton(
                                "SI, Terminar", callback_data="confirm_si"
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "NO, Continuar", callback_data="confirm_no"
                            )
                        ],
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(
                        "Por favor, selecciona una de las opciones propuestas.",
                        reply_markup=reply_markup,
                    )
                else:
                    logger.info(f"Pregunta fuera de tema de {user_id}: {message_text}")
                    await update.message.reply_text(
                        "Este chat está diseñado para responder preguntas sobre pediculosis y parasitismo. Por favor, formula una pregunta relacionada con estos temas."
                    )

    elif update.callback_query:
        query = update.callback_query
        user_id = query.from_user.id
        selected_option = query.data

        if user_id in usuarios:
            if selected_option == "volver_a_seleccionar":
                usuarios[user_id]["tema"] = None
                keyboard = [
                    [InlineKeyboardButton("Pediculosis", callback_data="pediculosis")],
                    [InlineKeyboardButton("Parasitismo", callback_data="parasitismo")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.reply_text(
                    f"Hola 🙋‍♂️ {capitalize_first_letter(usuarios[user_id]['name'])}, bienvenido a Pediculosis y Parasitismo Bot🤖. Escoge una de las siguientes opciones:",
                    reply_markup=reply_markup,
                )
            elif selected_option == "continuar_con_el_mismo":
                await query.message.reply_text(
                    f"Por favor, continúa formulando preguntas sobre {capitalize_first_letter(usuarios[user_id]['tema'])}."
                )
            elif selected_option == "confirm_si":
                await query.message.reply_text(
                    "Me alegra saber que todo ha sido claro. ¡Hasta luego!"
                )
                usuarios.pop(user_id)
            elif selected_option == "confirm_no":
                await query.message.reply_text(
                    "Por favor, dime en qué más puedo ayudarte."
                )
                usuarios[user_id]["esperando_confirmacion"] = False
            elif selected_option in ["pediculosis", "parasitismo"]:
                usuarios[user_id]["tema"] = selected_option
                await query.message.reply_text(
                    f"{capitalize_first_letter(usuarios[user_id]['name'])}, has seleccionado {selected_option}. ¿En qué puedo ayudarte?🤝"
                )
            await (
                query.answer()
            )  # Responder al callback para evitar que el botón quede en "cargando"


def main():
    # Cargar el token de la API de Telegram
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TELEGRAM_TOKEN:
        logger.error("Falta el TELEGRAM_TOKEN en el archivo .env")
        return

    # Crear el bot
    bot = Application.builder().token(TELEGRAM_TOKEN).build()

    # Función que se ejecuta cuando se recibe un mensaje
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    # Función que se ejecuta cuando se recibe un callback query
    bot.add_handler(CallbackQueryHandler(message_handler))

    # Ejecutar el bot
    logger.info("Iniciando el bot...")
    bot.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
