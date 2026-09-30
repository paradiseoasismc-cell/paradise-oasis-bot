import os
import uuid

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = -1003510243073

# ================= STORAGE =================
ORDERS = {}
USER_TO_ORDER = {}
ADMIN_ACTIVE = {}
LIFETIME_SALES = 0.0


# ================= ENTRY =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    text = (
        "🌴 Paradise Oasis Concierge 🌴\n\n"
        "Travel smarter. Not harder.\n"
        "Premium routes. Better prices. Same providers.\n\n"
        "👇 Choose a service to get started 👇"
    )

    keyboard = [
        [InlineKeyboardButton("🛒 Groceries", callback_data="svc_groceries")],
        [InlineKeyboardButton("🍔 Food Pickup / Delivery", callback_data="svc_food")],
        [InlineKeyboardButton("💳 Bills", callback_data="svc_bills")],
        [InlineKeyboardButton("🚗 Car Parts", callback_data="svc_carparts")],
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= SERVICE SELECT =================
async def service_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    context.user_data.clear()

    service = q.data.replace("svc_", "")
    context.user_data["service"] = service

    if service == "groceries":
        await groceries_start(q, context)

    elif service == "food":
        await food_start(q, context)

    elif service == "bills":
        await bills_start(q, context)

    elif service == "carparts":
        await carparts_start(q, context)


# ================= GROCERIES =================
async def groceries_start(q, context):
    context.user_data["step"] = "groceries_info"

    await q.message.reply_text(
        "🛒 Groceries\n\n"
        "• Stop & Shop only\n"
        "• 50% off\n\n"
        "📸 Send a screenshot of your grocery order/cart "
        "showing the items and total.\n\n"
        "Please do not send passwords or full payment-card information."
    )


# ================= FOOD =================
async def food_start(q, context):
    context.user_data["step"] = "food_info"

    await q.message.reply_text(
        "🍔 Food Pickup / Delivery\n\n"
        "📸 Send a screenshot of your food order/cart.\n\n"
        "Also tell us:\n"
        "• Pickup or delivery\n"
        "• Restaurant/store\n"
        "• Requested time"
    )


# ================= BILLS =================
async def bills_start(q, context):
    context.user_data["step"] = "bills_info"

    await q.message.reply_text(
        "💳 Bills\n\n"
        "📸 Send a screenshot of your bill showing:\n"
        "• Company\n"
        "• Amount due\n"
        "• Due date\n\n"
        "Please hide passwords, full account numbers, "
        "and payment-card information."
    )


# ================= CAR PARTS =================
async def carparts_start(q, context):
    context.user_data["step"] = "carparts_info"

    await q.message.reply_text(
        "🚗 Car Parts\n\n"
        "📸 Send a screenshot or link for the part you need.\n\n"
        "Also send:\n"
        "• Vehicle year\n"
        "• Make\n"
        "• Model\n"
        "• Quantity needed"
    )


# ================= TEXT ROUTER =================
async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    text = update.message.text

    # ================= ADMIN PRIVATE RELAY =================
    if uid in ADMIN_ACTIVE:
        oid = ADMIN_ACTIVE[uid]
        order = ORDERS.get(oid)

        if order and order["status"] != "CLOSED":
            await context.bot.send_message(
                order["user_id"],
                f"💬 Agent: {text}"
            )

        return

    # ================= CUSTOMER PRIVATE RELAY =================
    if uid in USER_TO_ORDER:
        oid = USER_TO_ORDER[uid]
        order = ORDERS.get(oid)

        if order and order["admin"] and order["status"] != "CLOSED":
            await context.bot.send_message(
                order["admin"],
                f"💬 Customer: {text}"
            )

        return

    step = context.user_data.get("step")

    # ================= SERVICE INFORMATION =================
    if step in [
        "groceries_info",
        "food_info",
        "bills_info",
        "carparts_info"
    ]:
        context.user_data["details"] = text
        context.user_data["step"] = "finalize"

        await finalize_order(update, context)
        return


# ================= PHOTO RELAY =================
async def photo_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    photo = update.message.photo[-1]

    # ================= ADMIN TO CUSTOMER =================
    if uid in ADMIN_ACTIVE:
        oid = ADMIN_ACTIVE[uid]
        order = ORDERS.get(oid)

        if order and order["status"] != "CLOSED":
            await context.bot.send_photo(
                order["user_id"],
                photo.file_id
            )

        return

    # ================= CUSTOMER TO ADMIN =================
    if uid in USER_TO_ORDER:
        oid = USER_TO_ORDER[uid]
        order = ORDERS.get(oid)

        if order and order["admin"] and order["status"] != "CLOSED":
            await context.bot.send_photo(
                order["admin"],
                photo.file_id
            )

        return


# ================= FINALIZE =================
async def finalize_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    oid = str(uuid.uuid4())[:8]

    service = context.user_data.get("service", "unknown")
    details = context.user_data.get("details", "")

    ORDERS[oid] = {
        "user_id": update.message.from_user.id,
        "admin": None,
        "status": "OPEN",
        "price": 0.0,
        "service": service,
        "details": details,
    }

    USER_TO_ORDER[update.message.from_user.id] = oid

    keyboard = [
        [
            InlineKeyboardButton(
                "👤 Claim",
                callback_data=f"claim_{oid}"
            )
        ],
        [
            InlineKeyboardButton(
                "💰 Paid",
                callback_data=f"paid_{oid}"
            ),
            InlineKeyboardButton(
                "❌ Unpaid",
                callback_data=f"unpaid_{oid}"
            ),
            InlineKeyboardButton(
                "🔒 Close",
                callback_data=f"close_{oid}"
            )
        ]
    ]

    service_names = {
        "groceries": "🛒 Groceries",
        "food": "🍔 Food Pickup / Delivery",
        "bills": "💳 Bills",
        "carparts": "🚗 Car Parts",
    }

    service_name = service_names.get(service, service)

    await context.bot.send_message(
        ADMIN_CHAT_ID,
        f"🆕 NEW ORDER #{oid}\n\n"
        f"📂 Service: {service_name}\n\n"
        f"📋 Customer details:\n{details}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text(
        "⏳ Your request has been received.\n\n"
        "An agent will review your request and connect with you here."
    )

    context.user_data.clear()


# ================= ADMIN ACTIONS =================
async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global LIFETIME_SALES

    q = update.callback_query
    await q.answer()

    action, oid = q.data.split("_", 1)

    order = ORDERS.get(oid)

    if not order:
        return

    # ================= CLAIM =================
    if action == "claim":

        # Don't allow a closed order to be claimed
        if order["status"] == "CLOSED":
            await q.message.reply_text(
                f"🔒 Order {oid} is already closed."
            )
            return

        order["admin"] = q.from_user.id
        ADMIN_ACTIVE[q.from_user.id] = oid

        await context.bot.send_message(
            order["user_id"],
            "👤 An agent has joined the chat.\n\n"
            "You can now communicate privately with your agent "
            "through this bot."
        )

        await q.message.reply_text(
            f"👤 Order {oid} claimed."
        )

    # ================= PAID =================
    elif action == "paid":

        order["status"] = "PAID"

        LIFETIME_SALES += order.get("price", 0.0)

        await q.message.reply_text(
            f"✅ Order {oid} marked PAID\n"
            f"💰 Price: ${order.get('price', 0.0):.2f}"
        )

        await context.bot.send_message(
            order["user_id"],
            f"✅ Your order #{oid} has been completed.\n\n"
            f"💰 Total: ${order.get('price', 0.0):.2f}"
        )

    # ================= UNPAID =================
    elif action == "unpaid":

        order["status"] = "UNPAID"

        await q.message.reply_text(
            f"❌ Order {oid} marked UNPAID"
        )

    # ================= CLOSE =================
    elif action == "close":

        order["status"] = "CLOSED"

        # Remove customer from active order
        user_id = order["user_id"]

        if USER_TO_ORDER.get(user_id) == oid:
            del USER_TO_ORDER[user_id]

        # Remove admin from active relay
        admin_id = order.get("admin")

        if admin_id and ADMIN_ACTIVE.get(admin_id) == oid:
            del ADMIN_ACTIVE[admin_id]

        await q.message.reply_text(
            f"🔒 Order {oid} closed.\n"
            f"💬 Private relay has been closed."
        )

        await context.bot.send_message(
            user_id,
            "🔒 This order has been closed.\n\n"
            "Thank you for using Paradise Oasis Concierge."
        )


# ================= PRICE COMMAND =================
async def set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id

    if uid not in ADMIN_ACTIVE:
        return

    try:
        price = float(context.args[0])

        oid = ADMIN_ACTIVE[uid]

        if oid not in ORDERS:
            return

        ORDERS[oid]["price"] = price

        await update.message.reply_text(
            f"💰 Price set: ${price:.2f}"
        )

    except (ValueError, IndexError):
        await update.message.reply_text(
            "Use the command like:\n"
            "/price 125.50"
        )


# ================= MAIN =================
def main():

    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    app = ApplicationBuilder().token(TOKEN).build()

    # START
    app.add_handler(
        CommandHandler("start", start)
    )

    # PRICE
    app.add_handler(
        CommandHandler("price", set_price)
    )

    # SERVICE SELECTION
    app.add_handler(
        CallbackQueryHandler(
            service_select,
            pattern="^svc_"
        )
    )

    # ADMIN ACTIONS
    app.add_handler(
        CallbackQueryHandler(
            admin_actions,
            pattern="^(claim|paid|unpaid|close)_"
        )
    )

    # PHOTOS
    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            photo_router
        )
    )

    # TEXT
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_router
        )
    )

    print("✅ Paradise Oasis Concierge running")

    app.run_polling()


if __name__ == "__main__":
    main()
