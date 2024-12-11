from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from database import store_user_info, mark_orphan_chosen, get_all_unchosen_orphan_ids, get_orphan_by_id
import sqlite3
# Your bot token
TOKEN = "Your Token"

# Define states
NAME, PHONE, CHOOSE_ORPHAN = range(3)

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_telegram_username = update.message.from_user.username  # Capture the Telegram username
    context.user_data['telegram_username'] = user_telegram_username  # Save Telegram username in context
    await update.message.reply_text(
        "Добро пожаловать! Пожалуйста, введите ваше имя."
    )
    return NAME

# Get user name
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.text
    context.user_data['name'] = user_name  # Save the user's name
    await update.message.reply_text("Спасибо! Пожалуйста, отправьте ваш номер телефона.")
    return PHONE

# Get phone number
# Get phone number
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone_number = update.message.text
    if phone_number:
        user_name = context.user_data['name']
        telegram_username = update.message.from_user.username  # Get Telegram username
        
        # Store user info and get the user_id
        user_id = store_user_info(user_name, phone_number, telegram_username)
        
        context.user_data['phone'] = phone_number  # Save phone number in user data
        await update.message.reply_text(f"Спасибо, {user_name}. Ваш номер телефона {phone_number} был сохранен.")

        # Get the list of unchosen orphans
        orphan_ids = get_all_unchosen_orphan_ids()
        if orphan_ids:
            # Create inline buttons for each orphan ID
            buttons = [[InlineKeyboardButton(str(i), callback_data=str(i))] for i in orphan_ids]
            inline_markup = InlineKeyboardMarkup(buttons)

            # Send message with only buttons (no text listing orphan IDs)
            await update.message.reply_text("Выберите ребенка:", reply_markup=inline_markup)

            return CHOOSE_ORPHAN
        else:
            await update.message.reply_text("Все дети были выбраны. Спасибо за вашу помощь!")
            return ConversationHandler.END
    else:
        await update.message.reply_text("Пожалуйста, отправьте ваш номер телефона.")
        return PHONE


# User selects an orphan
async def choose_orphan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge the button click

    orphan_id = query.data
    print(f"Received orphan ID: {orphan_id}")  # Debug log

    try:
        orphan_id = int(orphan_id)
        orphan = get_orphan_by_id(orphan_id)
        print(f"Fetched orphan data: {orphan}")  # Debug log

        if orphan:
            # Get user data
            user_name = context.user_data.get('name', 'Unknown User')
            user_phone = context.user_data.get('phone', 'Unknown Phone')
            telegram_username = context.user_data.get('telegram_username', 'Unknown Username')
            
            # Insert record into chosen_kids table
            orphan_name, orphan_age, orphan_gift = orphan[1], orphan[2], orphan[3]

            # Mark the orphan as chosen in your orphan table
            mark_orphan_chosen(orphan_id, user_name)  # Update orphan table

            # Create a new database connection and cursor for the insertion query
            conn = sqlite3.connect("orphans.db")
            cursor = conn.cursor()

            # Insert into the 'chosen_kids' table
            cursor.execute("""
                INSERT INTO chosen_kids (user_id, user_name, user_phone, telegram_username, orphan_id, orphan_name, orphan_gift)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_phone, user_name, user_phone, telegram_username, orphan_id, orphan_name, orphan_gift))
            conn.commit()

            print(f"Marked orphan {orphan_id} as chosen by {user_name}")  # Debug log

            # Edit the message to show the chosen orphan's details
            await query.edit_message_text(
                text=f"Вы выбрали ребенка:\nИмя: {orphan_name}\nВозраст: {orphan_age}\nПодарок: {orphan_gift}"
            )

            conn.close()  # Close the database connection

        else:
            print("Invalid orphan ID provided.")  # Debug log
            await query.edit_message_text(text="Ошибка. Пожалуйста, выберите существующего ребенка.")
    except Exception as e:
        print(f"Error in choose_orphan: {e}")  # Debug log for errors
        await query.edit_message_text(text="Произошла ошибка. Пожалуйста, попробуйте еще раз.")

    return ConversationHandler.END


def main():
    app = Application.builder().token(TOKEN).build()

    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            CHOOSE_ORPHAN: [CallbackQueryHandler(choose_orphan)],  # Remove per_message=True
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
