import logging
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient

# Configuration
BOT_TOKEN = "7873829431:AAFckz1ibUmRQn9plBkD6FN5VX1uQWv7HXE"
OWNER_ID = 6663845789 
MONGO_URI = "mongodb+srv://Cenzo:Cenzo123@cenzo.azbk1.mongodb.net/"
DB_NAME = "my_bot_db"

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_col = db["users"]
groups_col = db["groups"]
settings_col = db["settings"]

# Initialize logger
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user_type = "group" if update.effective_chat.type != "private" else "user"

    # Save user/group to MongoDB
    if user_type == "user":
        users_col.update_one({"_id": user_id}, {"$set": {"name": update.effective_user.full_name}}, upsert=True)
    else:
        groups_col.update_one({"_id": chat_id}, {"$set": {"name": update.effective_chat.title}}, upsert=True)

    # Fetch start message
    start_message = settings_col.find_one({"type": "start_message"})
    message = start_message["message"] if start_message else "Welcome to the bot!"

    await update.message.reply_text(message)

async def offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /offer command."""
    offer_message = settings_col.find_one({"type": "offer_message"})
    message = offer_message["message"] if offer_message else "No offers available at the moment."

    await update.message.reply_text(message)

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /contact command."""
    await update.message.reply_text("Contact the owner: @cenzeo")

async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /set command (owner only)."""
    if update.effective_user.id != OWNER_ID:
        return

    if context.args:
        message = " ".join(context.args)
    elif update.message.reply_to_message:
        message = update.message.reply_to_message.text
    else:
        await update.message.reply_text("Please provide or reply with a message to set.")
        return

    settings_col.update_one({"type": "start_message"}, {"$set": {"message": message}}, upsert=True)
    await update.message.reply_text("Start message updated!")

async def set_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /setoffer command (owner only)."""
    if update.effective_user.id != OWNER_ID:
        return

    if context.args:
        message = " ".join(context.args)
    elif update.message.reply_to_message:
        message = update.message.reply_to_message.text
    else:
        await update.message.reply_text("Please provide or reply with a message to set.")
        return

    settings_col.update_one({"type": "offer_message"}, {"$set": {"message": message}}, upsert=True)
    await update.message.reply_text("Offer message updated!")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /stats command (owner only)."""
    if update.effective_user.id != OWNER_ID:
        return

    total_users = users_col.count_documents({})
    total_groups = groups_col.count_documents({})
    await update.message.reply_text(f"Total users: {total_users}\nTotal groups: {total_groups}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /broadcast command (owner only)."""
    if update.effective_user.id != OWNER_ID:
        return

    if context.args:
        message = " ".join(context.args)
    elif update.message.reply_to_message:
        message = update.message.reply_to_message.text
    else:
        await update.message.reply_text("Please provide or reply with a message to broadcast.")
        return

    # Broadcast to users
    for user in users_col.find():
        try:
            await context.bot.send_message(chat_id=user["_id"], text=message)
        except Exception:
            pass

    # Broadcast to groups
    for group in groups_col.find():
        try:
            await context.bot.send_message(chat_id=group["_id"], text=message)
        except Exception:
            pass

    await update.message.reply_text("Broadcast completed!")

# Main function
def main() -> None:
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Public commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("offer", offer))
    application.add_handler(CommandHandler("contact", contact))

    # Owner commands
    application.add_handler(CommandHandler("set", set_command))
    application.add_handler(CommandHandler("setoffer", set_offer))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("broadcast", broadcast))

    # Set bot commands
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("offer", "View offers"),
        BotCommand("contact", "Contact the owner"),
        BotCommand("set", "Set start message (owner only)"),
        BotCommand("setoffer", "Set offer message (owner only)"),
        BotCommand("stats", "View stats (owner only)"),
        BotCommand("broadcast", "Broadcast message (owner only)"),
    ]
    application.bot.set_my_commands(commands)

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
