import os
import logging

from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from utils.utils_methods import (
    capitalize_first_letter,
    handle_user_message,
    mensaje_relacionado_con_temas,
    mensaje_de_despedida,
    generate_response,
    mensaje_relacionado_con_otro_tema,
    get_dialogflow_response,
)


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

usuarios = {}


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

            texto = [
                "imagen",
                "muéstrame imagenes",
                "muéstrame una imagen",
                "mostrar imagenes",
                "ver imagenes",
                "ver una imagen",
                "imagen",
                "foto",
                "ejemplo",
                "visual",
                "muestra",
                "piojos",
                "infografía",
                "muéstrame una imagen de pediculosis",
                "¿tienes fotos de piojos?",
                "dame un ejemplo visual de pediculosis",
                "quiero ver una infografía sobre pediculosis",
                "¿puedes mostrarme cómo se ven los piojos?",
                "¿tienes imágenes de los síntomas de pediculosis?",
                "muéstrame fotos de tratamientos para pediculosis",
                "¿qué aspecto tiene la pediculosis?",
                "quiero ver una imagen de cómo prevenir la pediculosis"
                # Imagenes parasitismo
                "imagen",
                "foto",
                "ejemplo",
                "visual",
                "muestra",
                "parásitos",
                "infografía",
                "muéstrame una imagen de parasitismo",
                "¿tienes fotos de parásitos?",
                "dame un ejemplo visual de parasitismo",
                "quiero ver una infografía sobre parasitismo",
                "¿puedes mostrarme cómo se ven los parásitos?",
                "¿tienes imágenes de los síntomas de parasitismo?",
                "muéstrame fotos de tratamientos para parasitismo",
                "¿qué aspecto tienen los parásitos?",
                "quiero ver una imagen de cómo prevenir el parasitismo"
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
