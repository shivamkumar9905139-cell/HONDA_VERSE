import os
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Dummy Database
users_db = {
    "balances": {},            # user_id: balance
    "stats": {},               # user_id: {wager, deposit, withdraw}
    "pending_withdrawals": {}, # user_id: amount
    "user_upi": {},            # user_id: upi_id
    "games_active": True       # Global game status
}

ADMIN_ID = 7995159553 # Admin Telegram ID[span_4](start_span)[span_4](end_span)[span_5](start_span)[span_5](end_span)
MIN_DEPOSIT = 80.0
MIN_WITHDRAW = 200.0

# --- /stop Command (Only Admin) ---
async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return await update.message.reply_text("❌ Dis command na only for admin[span_6](start_span)[span_6](end_span)[span_7](start_span)[span_7](end_span)!")
    
    await update.message.reply_text("🛑 Bot dey shut down now as admin command am...")
    os._exit(0)

# --- /panel Command (Admin Control Panel) ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return await update.message.reply_text("❌ Dis panel na only for admin[span_8](start_span)[span_8](end_span)[span_9](start_span)[span_9](end_span)!")
    
    status_text = "🟢 Running" if users_db["games_active"] else "🔴 Stopped"
    
    keyboard = [
        [
            InlineKeyboardButton("🛑 Stop Games", callback_data="admin_stop_games"),
            InlineKeyboardButton("▶️ Start Games", callback_data="admin_start_games")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"⚙️ **ADMIN CONTROL PANEL** ⚙️\n\n"
        f"🎮 Games Status: {status_text}\n"
        "Neeche buttons use to control games directly:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# --- /hb Command ---
async def hb_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🏛 **Bot Fund = $1,521**\n"
        "❄ **Active bet!**\n\n"
        "✨ **Honda Verse**"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# --- /start command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in users_db["balances"]:
        users_db["balances"][user.id] = 100.0 
        users_db["stats"][user.id] = {"wager": 0, "deposit": 0, "withdraw": 0}

    await update.message.reply_text(
        f"Namaste {user.first_name}! 🙏 Welcome to **Honda Verse**.\n\n"
        "🎮 You fit play Solo games, PvP/PvB and use Wallet commands.\n"
        "ℹ️ Type `/games` to see games or `/wallet` to check your wallet!",
        parse_mode="Markdown"
    )

# --- /wallet Command ---
async def wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = users_db["balances"].get(user_id, 0.0)
    saved_upi = users_db["user_upi"].get(user_id, "Set nahi hai")
    
    wallet_text = (
        f"👛 **HONDA VERSE WALLET** 👛\n\n"
        f"👤 **User:** {update.effective_user.first_name}\n"
        f"💰 **Current Balance:** ₹{bal}\n"
        f"💳 **Linked UPI:** `{saved_upi}`\n\n"
        f"📥 Min Deposit: ₹{MIN_DEPOSIT} | 📤 Min Withdraw: ₹{MIN_WITHDRAW}\n"
        "Use buttons below to deposit or withdraw:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("📥 Deposit", callback_data="wallet_deposit"),
            InlineKeyboardButton("📤 Withdraw", callback_data="wallet_withdraw")
        ],
        [
            InlineKeyboardButton("📊 My Stats", callback_data="wallet_stats"),
            InlineKeyboardButton("✏️ Set UPI", callback_data="set_upi_withdraw")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(wallet_text, reply_markup=reply_markup, parse_mode="Markdown")

# --- /games Command ---
async def games_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not users_db["games_active"]:
        return await update.message.reply_text("❌ Games are currently paused by admin!")
        
    games_text = (
        "🎮 **HONDA VERSE GAME CENTER** 🎮\n\n"
        "Available games:\n\n"
        "⚡ **Solo Games:**\n"
        "• `/limbo <amount>` - Limbo crash game\n"
        "• `/dr <amount> <low/high>` - Dice roll game\n\n"
        "💡 *Tip: Type `/wallet` to check balance!*"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🚀 Limbo", callback_data="play_limbo"),
            InlineKeyboardButton("🎲 Dice (DR)", callback_data="play_dr")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(games_text, reply_markup=reply_markup, parse_mode="Markdown")

# --- /mystats Command ---
async def mystats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = users_db["balances"].get(user_id, 0.0)
    st = users_db["stats"].get(user_id, {"wager": 0, "deposit": 0, "withdraw": 0})
    
    stats_text = (
        f"👤 **User Profile:** {update.effective_user.first_name}\n"
        f"💰 **Balance:** ₹{bal}\n"
        f"🎲 **Total Wager:** ₹{st['wager']}\n"
        f"📥 **Total Deposit:** ₹{st['deposit']}\n"
        f"📤 **Total Withdraw:** ₹{st['withdraw']}"
    )
    await update.message.reply_text(stats_text, parse_mode="Markdown")

# --- /deposit Command ---
async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("💳 Pay via UPI (Min ₹80)", callback_data="pay_upi")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"📥 **Deposit Money**\n\n"
        f"⚠️ **Minimum Deposit:** ₹{MIN_DEPOSIT}\n"
        "UPI ID: `Shudhanshu539@slc`\n\n"
        "Click button to pay and send screenshot here.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# --- /withdraw Command ---
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        amount = float(context.args[0])
    except (IndexError, ValueError):
        return await update.message.reply_text("⚠️ Format: `/withdraw amount` (Example: `/withdraw 300`)", parse_mode="Markdown")
    
    if amount < MIN_WITHDRAW:
        return await update.message.reply_text(f"❌ Minimum withdrawal amount na **₹{MIN_WITHDRAW}**!", parse_mode="Markdown")
    
    current_bal = users_db["balances"].get(user_id, 0.0)
    if amount > current_bal:
        return await update.message.reply_text("❌ You no get enough balance!")

    saved_upi = users_db["user_upi"].get(user_id, None)
    if not saved_upi:
        keyboard = [[InlineKeyboardButton("✏️ Set UPI ID First", callback_data="set_upi_withdraw")]]
        return await update.message.reply_text("❌ You never set your UPI ID! Click button to set am.", reply_markup=InlineKeyboardMarkup(keyboard))

    users_db["pending_withdrawals"][user_id] = amount

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve Withdraw", callback_data=f"appwit_{user_id}_{amount}"),
            InlineKeyboardButton("❌ Reject Withdraw", callback_data=f"rejwit_{user_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔔 **New Withdrawal Request**\n\n"
             f"👤 User: {update.effective_user.first_name} (`{user_id}`)\n"
             f"💰 Amount: ₹{amount}\n"
             f"💳 UPI ID: `{saved_upi}`",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    await update.message.reply_text(f"📤 Your withdrawal request of ₹{amount} don go to admin!")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    # Admin Panel Controls
    if data == "admin_stop_games" or data == "admin_start_games":
        if query.from_user.id != ADMIN_ID:
            return await query.answer("❌ Na only admin fit control dis!", show_alert=True)
        
        if data == "admin_stop_games":
            users_db["games_active"] = False
            await query.message.edit_text("🛑 Games have been STOPPED for all users.", parse_mode="Markdown")
        else:
            users_db["games_active"] = True
            await query.message.edit_text("▶️ Games have been STARTED for all users.", parse_mode="Markdown")
        return

    if data == "wallet_deposit":
        await deposit(update, context)
    elif data == "wallet_withdraw":
        await query.message.reply_text("To withdraw type: `/withdraw <amount>` (Example: `/withdraw 250`)")
    elif data == "wallet_stats":
        await mystats(update, context)
    elif data == "pay_upi":
        await query.message.reply_text(f"Please pay at `Shudhanshu539@slc` minimum **₹{MIN_DEPOSIT}** and send **screenshot** here.")
    elif data == "set_upi_withdraw":
        await query.message.reply_text("Send your UPI ID like dis: `/setupi your_upi@okhdfc`")
    elif data == "play_limbo":
        await limbo(update, context)
    elif data == "play_dr":
        await dr_game(update, context)
    
    # Admin Deposit Approve/Reject
    elif data.startswith("appdep_") or data.startswith("rejdep_"):
        if query.from_user.id != ADMIN_ID:
            return await query.answer("❌ Na only admin fit do dis!", show_alert=True)
        
        parts = data.split("_")
        action = parts[0]
        target_id = int(parts[1])
        
        if action == "appdep":
            await query.message.reply_text(f"✅ To approve deposit use command:\n`/addbal {target_id} <amount>`", parse_mode="Markdown")
        else:
            users_db.get("pending_withdrawals", {}).pop(target_id, None)
            await context.bot.send_message(chat_id=target_id, text="❌ Admin reject your deposit screenshot.")
            await query.message.edit_caption(caption=query.message.caption + "\n\n❌ **STATUS: REJECTED**")

    # Admin Withdrawal Approve/Reject
    elif data.startswith("appwit_") or data.startswith("rejwit_"):
        if query.from_user.id != ADMIN_ID:
            return await query.answer("❌ Na only admin fit do dis!", show_alert=True)
        
        parts = data.split("_")
        action = parts[0]
        target_id = int(parts[1])
        
        if action == "appwit":
            amount = float(parts[2])
            current_bal = users_db["balances"].get(target_id, 0.0)
            if current_bal >= amount:
                users_db["balances"][target_id] = current_bal - amount
                if target_id not in users_db["stats"]:
                    users_db["stats"][target_id] = {"wager": 0, "deposit": 0, "withdraw": 0}
                users_db["stats"][target_id]["withdraw"] += amount
                
                await context.bot.send_message(chat_id=target_id, text=f"✅ Your withdrawal of ₹{amount} don successfully transfer!")
                await query.edit_message_text(text=query.message.text + "\n\n✅ **STATUS: APPROVED & PROCESSED**", parse_mode="Markdown")
            else:
                await query.answer("❌ User no get dat amount for balance again!", show_alert=True)
        else:
            await context.bot.send_message(chat_id=target_id, text="❌ Admin reject your withdrawal request.")
            await query.edit_message_text(text=query.message.text + "\n\n❌ **STATUS: REJECTED**", parse_mode="Markdown")

async def set_upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        upi_id = context.args[0]
        users_db["user_upi"][user_id] = upi_id
        await update.message.reply_text(f"✅ Your UPI ID don save: `{upi_id}`\nNow you fit use `/withdraw amount`.", parse_mode="Markdown")
    except IndexError:
        await update.message.reply_text("⚠️ Format: `/setupi your_upi@okaxis`")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo = update.message.photo[-1].file_id
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Approve Deposit", callback_data=f"appdep_{user.id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"rejdep_{user.id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_photo(
        chat_id=ADMIN_ID, 
        photo=photo, 
        caption=f"🔔 **New Deposit Screenshot**\n"
                f"👤 User: {user.first_name} (`{user.id}`)\n\n"
                f"Use `/addbal {user.id} amount` to add balance after verify.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    await update.message.reply_text("⏳ Your deposit screenshot don go to admin. Balance go update soon!")

async def addbal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Na only admin fit use dis command!")
    try:
        target_id = int(context.args[0])
        amount = float(context.args[1])
        users_db["balances"][target_id] = users_db["balances"].get(target_id, 0.0) + amount
        if target_id not in users_db["stats"]:
            users_db["stats"][target_id] = {"wager": 0, "deposit": 0, "withdraw": 0}
        users_db["stats"][target_id]["deposit"] += amount
        
        await update.message.reply_text(f"✅ Added ₹{amount} to user `{target_id}`.", parse_mode="Markdown")
        await context.bot.send_message(chat_id=target_id, text=f"🎉 Admin don approve your deposit of ₹{amount} and add am!")
    except Exception:
        await update.message.reply_text("⚠️ Format: `/addbal userid amount`", parse_mode="Markdown")

async def cutbal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Na only admin fit use dis command!")
    try:
        target_id = int(context.args[0])
        amount = float(context.args[1])
        users_db["balances"][target_id] = max(0.0, users_db["balances"].get(target_id, 0.0) - amount)
        await update.message.reply_text(f"✅ Deducted ₹{amount} from user `{target_id}`.", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("⚠️ Format: `/cutbal userid amount`", parse_mode="Markdown")

async def limbo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not users_db["games_active"]:
        return await update.message.reply_text("❌ Games are currently paused by admin!")
    multiplier = random.uniform(1.0, 15.0)
    if multiplier > 10.0:
        result_text = f"💥 **Crash!** Multiplier: {multiplier:.2f}x (You lose ❌)"
    else:
        result_text = f"🎉 **Won!** Multiplier: {multiplier:.2f}x (You win ✅)"
    
    await update.message.reply_text(f"🚀 **Limbo Game**\n\n{result_text}", parse_mode="Markdown")

async def dr_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not users_db["games_active"]:
        return await update.message.reply_text("❌ Games are currently paused by admin!")
    dice_roll = random.randint(1, 6)
    await update.message.reply_text(f"🎲 Dice rolled: **{dice_roll}**")


if __name__ == '__main__':
    TOKEN = os.environ.get("TOKEN", "8827781937:AAFdd8YqBDTOqKg8ER43FCKCjYZ3WWuwcyU")
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("stop", stop_bot))
    app.add_handler(CommandHandler("panel", admin_panel))
    app.add_handler(CommandHandler("hb", hb_command))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("wallet", wallet_command))
    app.add_handler(CommandHandler("games", games_menu))
    app.add_handler(CommandHandler("mystats", mystats))
    app.add_handler(CommandHandler("deposit", deposit))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CommandHandler("setupi", set_upi))
    app.add_handler(CommandHandler("addbal", addbal))
    app.add_handler(CommandHandler("cutbal", cutbal))
    app.add_handler(CommandHandler("limbo", limbo))
    app.add_handler(CommandHandler("dr", dr_game))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🚀 Honda Verse Bot with Admin Panel & Stop command is running...")
    app.run_polling()
