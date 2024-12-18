import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from database import store_user_info, mark_orphan_chosen, get_all_unchosen_orphan_ids, get_orphan_by_id
import sqlite3
import boto3 

# Your bot token
TOKEN = "Of_course_i_will_not_tell"  # Replace with your bot token

# Set up logging
logging.basicConfig(
    filename="bot_activity.log",
    level=logging.WARNING,  # Only log WARNING and above by default
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Define states
NAME, PHONE, CHOOSE_ORPHAN, HELP_MORE = range(4)

S3_BUCKET_NAME = "will_not_tell"  # Replace with your bucket name
S3_REGION = "Frankfurt"  # Replace with your S3 bucket region

s3_client = boto3.client('s3')

# Function to upload files to S3
def upload_to_s3(file_name, bucket_name, object_name):
    try:
        s3_client.upload_file(file_name, bucket_name, object_name)
        logging.warning(f"File {file_name} uploaded to S3 bucket {bucket_name} as {object_name}.")
    except Exception as e:
        logging.error(f"Failed to upload {file_name} to S3: {e}")


# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_telegram_username = update.message.from_user.username  # Capture the Telegram username
    context.user_data['telegram_username'] = user_telegram_username  # Save Telegram username in context
    logging.warning(f"User {user_telegram_username} started the conversation.")  # Log user start
    await update.message.reply_text(
        """
Привет, дорогой Дед Мороз🎅!
Спасибо за поддержку традиции _«ARMAN – 2024»_✨!
Сначала просим тебя ознакомиться с правилами «ARMAN – 2024» в описании канала.
*Если ты уже ознакомился, то напиши мне свое имя*😊
        """, parse_mode='Markdown'
    )
    return NAME

# Get user name
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.text
    context.user_data['name'] = user_name  # Save the user's name
    logging.warning(f"User {context.user_data['telegram_username']} provided their name: {user_name}")  # Log name input
    await update.message.reply_text(
        """ 
Рады знакомству!
Время доставки подарка🎁:            ❗️*ДО 25 декабря (среда)*❗️
Адрес доставки: Общественный фонд «Бақытты шаңырақ», пр. Ракымжан Кошкарбаев, дом 60, 1 этаж, НП № 5
Ссылка на 2ГИС: https://2gis.kz/astana/geo/70000001065251665


*Чтобы, продолжить пожалуйста свой номер телефона для связи.*
        """, parse_mode='Markdown'
    )
    return PHONE

# Get phone number
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone_number = update.message.text
    if phone_number:
        user_name = context.user_data['name']
        telegram_username = context.user_data['telegram_username']

        # Store user info and get the user_id
        user_id = store_user_info(user_name, phone_number, telegram_username)
        context.user_data['phone'] = phone_number  # Save phone number in user data

        logging.warning(f"User {telegram_username} provided phone number: {phone_number}")  # Log phone input
        await update.message.reply_text(f"Спасибо, {user_name}. Ваш номер телефона {phone_number} был сохранен.")

        # Show unchosen orphans
        orphan_ids = get_all_unchosen_orphan_ids()
        if orphan_ids:
            buttons = [[InlineKeyboardButton(str(i), callback_data=str(i))] for i in orphan_ids]
            inline_markup = InlineKeyboardMarkup(buttons)
            await update.message.reply_text("Выбери номер ребенка из 275 писем. Просто нажми на число, которое тебе по душе!", reply_markup=inline_markup)
            return CHOOSE_ORPHAN
        else:
            await update.message.reply_text("🎉Ура🎉! Все дети нашли своих Дедов Морозов, и ни один не остался без внимания! Благодарим каждого  за вашу доброту и поддержку!")
            return ConversationHandler.END
    else:
        await update.message.reply_text("Пожалуйста, отправьте ваш номер телефона.")
        return PHONE

# Handle orphan selection
# Handle orphan selection with checking if the orphan has already been chosen
async def choose_orphan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge the button click

    orphan_id = query.data
    try:
        orphan_id = int(orphan_id)

        # Check if the orphan has already been chosen
        conn = sqlite3.connect("orphans.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chosen_kids WHERE orphan_id = ?", (orphan_id,))
        orphan_exists = cursor.fetchone()  # Check if the orphan has already been chosen
        conn.close()

        if orphan_exists:
            # If already chosen, send a message to the user to choose a different orphan
            await query.edit_message_text("О нет, кто-то прямо сейчас уже выбрал этот номер, выбери другой.")
            orphan_ids = get_all_unchosen_orphan_ids()  # Get new list of unchosen orphans
            buttons = [[InlineKeyboardButton(str(i), callback_data=str(i))] for i in orphan_ids]
            inline_markup = InlineKeyboardMarkup(buttons)
            await query.message.reply_text("Выбери другой номер ребенка из 275 писем.", reply_markup=inline_markup)
            return CHOOSE_ORPHAN  # Let the user choose again
        else:
            # Proceed with orphan selection if not already chosen
            orphan = get_orphan_by_id(orphan_id)
            if orphan:
                user_name = context.user_data['name']
                user_phone = context.user_data['phone']
                telegram_username = context.user_data['telegram_username']

                orphan_name, orphan_age, orphan_gift, orphan_parent_phone, orphan_hyper_link = (
                    orphan[1], orphan[2], orphan[3], orphan[4], orphan[5]
                )

                # Mark orphan as chosen
                mark_orphan_chosen(orphan_id, user_name)

                # Insert into database
                conn = sqlite3.connect("orphans.db")
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO chosen_kids (user_id, user_name, user_phone, telegram_username, orphan_id, orphan_name, orphan_gift, orphan_parent_phone, orphan_hyper_link)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_phone, user_name, user_phone, telegram_username, orphan_id, orphan_name, orphan_gift, orphan_parent_phone, orphan_hyper_link))
                conn.commit()
                conn.close()

                upload_to_s3("chosen_kids.xlsx", S3_BUCKET_NAME, "chosen_kids.xlsx")
                upload_to_s3("orphans.xlsx", S3_BUCKET_NAME, "orphans.xlsx")

                logging.warning(f"User {telegram_username} chose orphan: {orphan_name} (ID: {orphan_id})")  # Log orphan selection

                await query.edit_message_text(
                    text=(
                        f"🎉Поздравляем🎉!\n"
                        f"❗️Важно❗️обязательно подписывай свои подарки номером письма (Формат: №{orphan_id}, {orphan_name}), чтобы он не потерялся среди остальных \n"
                        f"Ты стал Дедом Морозом для:\n"
                        f"Имя: {orphan_name}\n"
                        f"Номер письма: {orphan_id}\n"
                        f"Возраст: {orphan_age}\n"
                        f"Подарок мечты: {orphan_gift}\n"
                        f"Номер родителя: {orphan_parent_phone}\n"
                        f"Ссылка на его письмо Деду Морозу: {orphan_hyper_link}\n\n"
                        """Если у тебя возникнут вопросы, ты можешь обратиться к организаторам «ARMAN» по номеру +7 775 987 6258. Пусть детские мечты сбываются! Искренне, твой «ARMAN»!"""
                        
                    )
                )

                # Ask if user wants to help more
                buttons = [
                    [InlineKeyboardButton("Да", callback_data="yes"), InlineKeyboardButton("Нет", callback_data="no")]
                ]
                inline_markup = InlineKeyboardMarkup(buttons)
                await query.message.reply_text("Хочешь ли ты исполнить желание еще одного ребенка?", reply_markup=inline_markup)
                return HELP_MORE
            else:
                await query.edit_message_text("Ошибка. Пожалуйста, выберите существующего ребенка.")
    except ValueError as e:
        logging.warning(f"Error in choose_orphan: {e}")  # Log error
        await query.edit_message_text("Произошла ошибка. Пожалуйста, попробуйте снова.")
    return ConversationHandler.END



# Handle "help more" response
async def help_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "yes":
        orphan_ids = get_all_unchosen_orphan_ids()
        if orphan_ids:
            buttons = [[InlineKeyboardButton(str(i), callback_data=str(i))] for i in orphan_ids]
            inline_markup = InlineKeyboardMarkup(buttons)
            await query.message.reply_text("Выбери номер ребенка:", reply_markup=inline_markup)
            return CHOOSE_ORPHAN
        else:
            await query.message.reply_text("Все дети были выбраны. Спасибо за вашу помощь!")
            return ConversationHandler.END
    elif query.data == "no":
        logging.warning(f"User {context.user_data['telegram_username']} finished helping.")  # Log user decision
        await query.message.reply_text("Спасибо за твою помощь! Пусть мечты сбываются!")
        return ConversationHandler.END

# Main function
def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            CHOOSE_ORPHAN: [CallbackQueryHandler(choose_orphan)],
            HELP_MORE: [CallbackQueryHandler(help_more)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
