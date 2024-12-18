import os
import logging
import asyncio

from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from fastapi import FastAPI
import uvicorn
from utils.utils_methods import (
    capitalize_first_letter,
    handle_user_message,
    mensaje_relacionado_con_temas,
    mensaje_de_despedida,
    generate_response,
    mensaje_relacionado_con_otro_tema,
    get_dialogflow_response,
)

# Configuración de FastAPI
app = FastAPI()


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

usuarios = {}
bot = None  # Mover la declaración del bot aquí


# Función que se ejecuta cuando se recibe un mensaje
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    logger.info(f"Mensaje recibido: {user_message}")
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

            texto = [
                "imagen",
                "muéstrame imagenes",
                "muéstrame una imagen",
                "mostrar imagenes",
                "ver imagenes",
                "ver una imagen",
            ]
            # Verificar si el mensaje es una solicitud de imágenes
            if any(palabra in message_text for palabra in texto):
                dialogflow_response = get_dialogflow_response(message_text)

                # Filtrar las imágenes según el tema seleccionado
                mensajes_filtrados = [
                    msg
                    for msg in dialogflow_response
                    if msg.get("title", "").lower() == tema_actual
                ]

                if mensajes_filtrados:
                    for msg in mensajes_filtrados:
                        if msg["type"] == "combined":
                            await update.message.reply_photo(
                                photo=msg["photo"],
                                caption=msg["text"],
                                reply_markup=InlineKeyboardMarkup([msg["buttons"]]),
                            )
                        else:
                            await update.message.reply_text(msg["text"])
                else:
                    await update.message.reply_text(
                        f"No se encontraron imágenes para el tema {tema_actual}."
                    )
                return  # Terminar el manejo aquí

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


# Iniciar el bot en el evento de inicio de FastAPI
@app.on_event("startup")
async def startup_event():
    global bot
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TELEGRAM_TOKEN:
        logger.error("Falta el TELEGRAM_TOKEN en el archivo .env")
        return

    # Crear el bot
    bot = Application.builder().token(TELEGRAM_TOKEN).build()

    # Agregar handlers
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    bot.add_handler(CallbackQueryHandler(message_handler))

    # Iniciar el bot en modo asincrónico
    logger.info("Iniciando el bot...")
    await bot.initialize()  # Inicializar la aplicación
    asyncio.create_task(
        bot.updater.start_polling()
    )  # Comenzar a recibir actualizaciones


@app.get("/")
async def root():
    return {"message": "Bot de Telegram activo en Render"}


# Ejecutar el servidor con Uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
