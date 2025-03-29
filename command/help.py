from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def handle_help(client, message):
    # Crear el teclado InlineKeyboardMarkup
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Ayuda 1", callback_data="help_1")],
            [InlineKeyboardButton("Ayuda 2", callback_data="help_2")],
            [InlineKeyboardButton("Ayuda 3", callback_data="help_3")]
        ]
    )
    await message.reply_text(
        "Selecciona una opción para obtener más ayuda:",
        reply_markup=keyboard
    )

async def handle_help_callback(client, callback_query):
    # Procesar las acciones de los botones
    data = callback_query.data

    if data == "help_1":
        await callback_query.message.edit_text(
            "Texto de Ayuda 1:\nAquí encuentras información detallada sobre la primera opción.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Volver", callback_data="help_back")]]
            )
        )
        await callback_query.answer("Mostrando Ayuda 1.")

    elif data == "help_2":
        await callback_query.message.edit_text(
            "Texto de Ayuda 2:\nDetalles importantes sobre la segunda opción que seleccionaste.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Volver", callback_data="help_back")]]
            )
        )
        await callback_query.answer("Mostrando Ayuda 2.")

    elif data == "help_3":
        await callback_query.message.edit_text(
            "Texto de Ayuda 3:\nExplicación relacionada con la tercera opción.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Volver", callback_data="help_back")]]
            )
        )
        await callback_query.answer("Mostrando Ayuda 3.")

    elif data == "help_back":
        # Volver al menú principal de ayuda
        await callback_query.message.edit_text(
            "Selecciona una opción para obtener más ayuda:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Ayuda 1", callback_data="help_1")],
                    [InlineKeyboardButton("Ayuda 2", callback_data="help_2")],
                    [InlineKeyboardButton("Ayuda 3", callback_data="help_3")]
                ]
            )
        )
        await callback_query.answer("Regresando al menú principal.")
  
