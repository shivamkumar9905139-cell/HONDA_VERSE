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
    "user_upi": {}             # user_id: upi_id
}

ADMIN_ID = 7995159553 # Aapki Admin Telegram ID
MIN_DEPOSIT = 80.0
MIN_WITHDRAW = 200.0

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
        users_db["balances"][user.id] = 100.0 # Free starting bonus
        users_db["stats"][user.id] = {"wager": 0, "deposit": 0, "withdraw": 0}

    await update.message.reply_text(
        f"Namaste {user.first_name}! 🙏 Swagat hai **Honda Verse** mein.\n\n"
        "🎮 Aap yahan Solo games, PvP/PvB aur Wallet commands use kar sakte hain.\n"
        "ℹ️ Games dekhne ke liye `/games` type karein ya `/hb` try karein!",
        parse_mode="Markdown"
    )

# --- /games Command (Game List Menu) ---
async def games_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    games_text = (
        "🎮 **HONDA VERSE GAME CENTER** 🎮\n\n"
        "Neeche diye gaye games aap khel sakte hain:\n\n"
        "⚡ **Solo Games:**\n"
        "• `/rain <amount> <member>` - Rain amount distribute karein\n"
        "• `/escrow <amount>` - Escrow button game\n"
        "• `/limbo <amount>` - Limbo crash game (10x+ target rule)\n"
        "• `/dr <amount> <low/high/odd/even>` - Dice roll game\n"
        "• `/mines <amount>` - Mines bomb game\n"
        "• `/tower <amount>` - Tower climbing game\n\n"
        "⚔️ **PvP / PvB Games:**\n"
        "• `/dice <amount> <round>` - Dice battle\n"
        "• `/slots <amount>` - Slots game\n"
        "• `/basketball <amount>` - Basketball dice game\n"
        "• `/bowl <amount>` - Bowling game\n"
        "• `/darts <amount>` - Darts game\n\n"
        "💡 *Tip: Kisi bhi game ko khelne ke liye uska command aur amount likhein!* "
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🚀 Limbo", callback_data="play_limbo"),
            InlineKeyboardButton("🎲 Dice (DR)", callback_data="play_dr")
        ],
        [
            InlineKeyboardButton("💣 Mines", callback_data="play_mines"),
            InlineKeyboardButton("🗼 Tower", callback_data="play_tower")
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

# --- /deposit Command (Min ₹80) ---
async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("💳 Pay via UPI (Min ₹80)", callback_data="pay_upi")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"📥 **Deposit Money**\n\n"
        f"⚠️ **Minimum Deposit:** ₹{MIN_DEPOSIT}\n"
        "UPI ID: `Shudhanshu539@slc`\n\n"
        "Button par click karke payment karein aur payment ka screenshot yahan bhej dein.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# --- /withdraw Command (Min ₹200) ---
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        amount = float(context.args[0])
    except (IndexError, ValueError):
        return await update.message.reply_text("⚠️ Format: `/withdraw amount` (Jaise: `/withdraw 300`)", parse_mode="Markdown")
    
    if amount < MIN_WITHDRAW:
        return await update.message.reply_text(f"❌ Minimum withdrawal amount **₹{MIN_WITHDRAW}** hai!", parse_mode="Markdown")
    
    current_bal = users_db["balances"].get(user_id, 0.0)
    if amount > current_bal:
        return await update.message.reply_text("❌ Aapke account mein itna balance nahi hai!")

    saved_upi = users_db["user_upi"].get(user_id, None)
    if not saved_upi:
        keyboard = [[InlineKeyboardButton("✏️ Set UPI ID First", callback_data="set_upi_withdraw")]]
        return await update.message.reply_text("❌ Aapne apni UPI ID set nahi ki hai! Pehle button dabakar UPI ID set karein.", reply_markup=InlineKeyboardMarkup(keyboard))

    users_db["pending_withdrawals"][user_id] = amount

    # Admin ko withdrawal request bhejna with buttons
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

    await update.message.reply_text(f"📤 Aapki ₹{amount} ki withdrawal request admin ke paas bhej di gayi hai!")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "pay_upi":
        await query.message.reply_text(f"Kripya `Shudhanshu539@slc` par kam se kam **₹{MIN_DEPOSIT}** pay karke uska **screenshot** chat mein upload karein.")
    elif data == "set_upi_withdraw":
        await query.message.reply_text("Kripya apni UPI ID bhejein is format mein: `/setupi aapki_upi@okhdfc`")
    elif data == "play_limbo":
        await query.message.reply_text("Limbo khelne ke liye type karein: `/limbo <amount>`")
    elif data == "play_dr":
        await query.message.reply_text("Dice khelne ke liye type karein: `/dr <amount> low`")
    
    # Admin Deposit Approve/Reject
    elif data.startswith("appdep_") or data.startswith("rejdep_"):
        if query.from_user.id != ADMIN_ID:
            return await query.answer("❌ Yeh sirf admin ke liye hai!", show_alert=True)
        
        parts = data.split("_")
        action = parts[0]
        target_id = int(parts[1])
        
        if action == "appdep":
            # Prompt admin to enter amount or default logic
            await query.message.reply_text(f"✅ Deposit approve karne ke liye command use karein:\n`/addbal {target_id} <amount>`", parse_mode="Markdown")
        else:
            users_db.get("pending_withdrawals", {}).pop(target_id, None)
            await context.bot.send_message(chat_id=target_id, text="❌ Aapka deposit screenshot admin dwara reject kar diya gaya.")
            await query.message.edit_caption(caption=query.message.caption + "\n\n❌ **STATUS: REJECTED**")

    # Admin Withdrawal Approve/Reject
    elif data.startswith("appwit_") or data.startswith("rejwit_"):
        if query.from_user.id != ADMIN_ID:
            return await query.answer("❌ Yeh sirf admin ke liye hai!", show_alert=True)
        
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
                
                await context.bot.send_message(chat_id=target_id, text=f"✅ Aapka ₹{amount} ka withdrawal successfully transfer kar diya gaya hai!")
                await query.edit_message_text(text=query.message.text + "\n\n✅ **STATUS: APPROVED & PROCESSED**", parse_mode="Markdown")
            else:
                await query.answer("❌ User ke paas ab itna balance nahi hai!", show_alert=True)
        else:
            await context.bot.send_message(chat_id=target_id, text="❌ Aapka withdrawal request admin dwara reject kar diya gaya.")
            await query.edit_message_text(text=query.message.text + "\n\n❌ **STATUS: REJECTED**", parse_mode="Markdown")

async def set_upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        upi_id = context.args[0]
        users_db["user_upi"][user_id] = upi_id
        await update.message.reply_text(f"✅ Aapki UPI ID successfully save ho gayi hai: `{upi_id}`\nAb aap `/withdraw amount` command use kar sakte hain.", parse_mode="Markdown")
    except IndexError:
        await update.message.reply_text("⚠️ Format: `/setupi your_upi@okaxis`")

# Handling Screenshot/Photo for Deposit Request
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
                f"Verify karke balance add karne ke liye `/addbal {user.id} amount` use karein.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    await update.message.reply_text("⏳ Aapka deposit screenshot admin ke paas bhej diya gaya hai. Verify hone par balance add ho jayega!")

# --- Admin Balance Controls (/addbal & /cutbal) ---
async def addbal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Yeh command sirf admin ke liye hai!")
    try:
        target_id = int(context.args[0])
        amount = float(context.args[1])
        users_db["balances"][target_id] = users_db["balances"].get(target_id, 0.0) + amount
        if target_id not in users_db["stats"]:
            users_db["stats"][target_id] = {"wager": 0, "deposit": 0, "withdraw": 0}
        users_db["stats"][target_id]["deposit"] += amount
        
        await update.message.reply_text(f"✅ Successfully added ₹{amount} to user `{target_id}`.", parse_mode="Markdown")
        await context.bot.send_message(chat_id=target_id, text=f"🎉 Aapka deposit ₹{amount} admin dwara approve aur add kar diya gaya hai!")
    except Exception:
        await update.message.reply_text("⚠️ Format: `/addbal userid amount`", parse_mode="Markdown")

async def cutbal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Yeh command sirf admin ke liye hai!")
    try:
        target_id = int(context.args[0])
        amount = float(context.args[1])
        users_db["balances"][target_id] = max(0.0, users_db["balances"].get(target_id, 0.0) - amount)
        await update.message.reply_text(f"✅ Successfully deducted ₹{amount} from user `{target_id}`.", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("⚠️️ Format: `/cutbal userid amount`", parse_mode="Markdown")

# --- Solo Games: Limbo ---
async def limbo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    multiplier = random.uniform(1.0, 15.0)
    if multiplier > 10.0:
        result_text = f"💥 **Crash!** Multiplier: {multiplier:.2f}x (10x se upar gaya aur fhoot gaya! Haar gaye ❌)"
    else:
        result_text = f"🎉 **Won!** Multiplier: {multiplier:.2f}x (Safe rahe, jeet gaye! ✅)"
    
    await update.message.reply_text(f"🚀 **Limbo Game**\n\n{result_text}", parse_mode="Markdown")

# --- Solo Game: Dice / DR ---
async def dr_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dice_roll = random.randint(1, 6)
    await update.message.reply_text(f"🎲 Dice rolled: **{dice_roll}**")


if __name__ == '__main__':
    TOKEN = os.environ.get("TOKEN", "8827781937:AAEpV-EL_YY3MZ-70jaA0Rq5ZXFFotrp_D4")
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Handlers Registration
    app.add_handler(CommandHandler("hb", hb_command))
    app.add_handler(CommandHandler("start", start))
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
    
    print("🚀 Honda Verse Casino Bot with full admin approval system is running...")
    app.run_polling()
