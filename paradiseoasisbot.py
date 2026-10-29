
import os
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = -1003510243073
ORDERS, USER_TO_ORDER, ADMIN_ACTIVE = {}, {}, {}
LIFETIME_SALES = 0.0

SERVICES = {
    "flights": "✈️ Flights",
    "groceries": "🛒 Groceries",
    "food": "🍔 Food Pickup / Delivery",
    "fooddrinks": "🍽️ Food & Drinks",
    "bills": "💳 Bills",
    "carparts": "🚗 Car Parts",
    "gas": "⛽ Gas",
    "skiing": "🎢 Skiing & Amusement Parks",
    "gym": "🏋️ Gym Memberships",
    "games": "🎮 PSN & Xbox Games",
}

RESTAURANTS = [
    ("jerseymikes", "Jersey Mike’s"),
    ("dominos", "Domino’s"),
    ("chipotle", "Chipotle / Tacos"),
    ("breakfast", "Breakfast"),
    ("sonic", "Sonic"),
    ("steakhouse", "Steakhouse"),
    ("hibachi", "Hibachi"),
    ("cava", "CAVA"),
    ("dinein", "Dine-In Restaurants"),
    ("panda", "Panda Express"),
    ("chinese", "Chinese Food"),
    ("wingstop", "Wingstop"),
]
REST_NAMES = dict(RESTAURANTS)


def main_keyboard():
    buttons = [
        InlineKeyboardButton(name, callback_data=f"svc_{key}")
        for key, name in SERVICES.items()
    ]
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    rows.append([
        InlineKeyboardButton(
            "📢 Latest Updates",
            url="https://t.me/paradiseoasisupdates"
        )
    ])
    return InlineKeyboardMarkup(rows)


def restaurant_keyboard():
    buttons = [
        InlineKeyboardButton(name, callback_data=f"rest_{key}")
        for key, name in RESTAURANTS
    ]
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    rows.append([
        InlineKeyboardButton(
            "⬅️ Back to Main Menu",
            callback_data="back_main"
        )
    ])
    return InlineKeyboardMarkup(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🌴 Paradise Oasis Concierge 🌴\n\n"
        "Travel smarter. Not harder.\n"
        "Premium routes. Better prices. Same providers.\n\n"
        "👇 Choose a service to get started 👇",
        reply_markup=main_keyboard()
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "👇 Choose a service to get started 👇",
        reply_markup=main_keyboard()
    )


async def service_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    key = q.data[4:]

    context.user_data.clear()
    context.user_data["service"] = key

    if key == "fooddrinks":
        await q.message.reply_text(
            "🍽️ Food & Drinks\n\n"
            "Choose a restaurant or food category:",
            reply_markup=restaurant_keyboard()
        )
        return

    prompts = {
        "flights": (
            "✈️ Flights\n\n"
            "📸 Send screenshot(s) of the itinerary or options "
            "you want help with. An agent will discuss necessary "
            "trip details privately.\n\n"
            "Please don't send payment-card details or passwords."
        ),
        "groceries": (
            "🛒 Groceries\n\n"
            "• Stop & Shop only\n"
            "• 50% off\n\n"
            "📸 Send a screenshot of your cart showing items and total.\n\n"
            "Please don't send passwords or full payment-card information."
        ),
        "food": (
            "🍔 Food Pickup / Delivery\n\n"
            "📸 Send a screenshot of your food order/cart.\n\n"
            "Also tell us the restaurant/store, pickup or delivery, "
            "and requested time."
        ),
        "bills": (
            "💳 Bills\n\n"
            "📸 Send a screenshot showing the company, amount due, "
            "and due date.\n\n"
            "Hide passwords, full account numbers, and payment-card information."
        ),
        "carparts": (
            "🚗 Car Parts\n\n"
            "📸 Send a screenshot of the part you need, plus vehicle "
            "year, make, model, and quantity."
        ),
        "gas": (
            "⛽️ Gas 50% OFF ⛽️\n\n"
            "📌 Must be a Shell Gas Station\n"
            "📌 $30 minimum (50%OFF)\n"
            "📌 Tell Support what Pump # you are parked at\n"
            "📌Automatically Works\n\n"
            "📸 Send a screenshot or message Support with your request."
        ),
        "skiing": (
            "🎢 Skiing & Amusement Parks\n\n"
            "📸 Send a screenshot of the ticket, plan, or offer "
            "you want help with."
        ),
        "gym": (
            "🏋️ Gym Memberships\n\n"
            "50% off.\n"
            "📸 Send a screenshot of the plan and tell us which gym you selected."
        ),
        "games": (
            "🎮 PSN & Xbox Games\n\n"
            "📸 Send a screenshot of the game or offer you want help with."
        ),
    }

    context.user_data["step"] = "info"
    await q.message.reply_text(
        prompts.get(key, "📸 Send a screenshot or details of your request.")
    )


async def restaurant_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    key = q.data[5:]

    if key not in REST_NAMES:
        return

    context.user_data.clear()
    context.user_data.update(
        service="fooddrinks",
        restaurant=REST_NAMES[key],
        step="info"
    )

    if key == "dinein":
        prompt = (
            "🍽️ Dine-In Restaurants\n\n"
            "Send a screenshot of the restaurant QR code or send "
            "the menu/order link. An agent will connect with you "
            "to discuss details and final price."
        )
    else:
        prompt = (
            f"🍽️ {REST_NAMES[key]}\n\n"
            "📸 Send a screenshot of the menu, order, or items you want. "
            "An agent will connect with you to discuss details and final price."
        )

    await q.message.reply_text(prompt)


async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data.clear()
    await q.message.reply_text(
        "👇 Choose a service to get started 👇",
        reply_markup=main_keyboard()
    )


def active_order(uid):
    oid = USER_TO_ORDER.get(uid)
    return oid, ORDERS.get(oid) if oid else None


async def create_order(message, context, details, photo_id=None):
    uid = message.from_user.id
    old_id, old = active_order(uid)

    if old and old.get("status") != "CLOSED":
        if photo_id:
            await context.bot.send_photo(
                ADMIN_CHAT_ID,
                photo_id,
                caption=f"📎 Additional screenshot for order #{old_id}"
            )
        if details:
            old["details"] = (
                old.get("details", "") + "\n" + details
            ).strip()
        await message.reply_text(
            f"Your request is already open as order #{old_id}. "
            "Your details have been added."
        )
        return

    oid = str(uuid.uuid4())[:8]
    service = context.user_data.get("service", "unknown")
    restaurant = context.user_data.get("restaurant")
    label = (
        f"🍽️ Food & Drinks — {restaurant}"
        if restaurant else SERVICES.get(service, service)
    )

    ORDERS[oid] = {
        "user_id": uid,
        "admin": None,
        "status": "OPEN",
        "price": None,
        "sale_counted": False,
        "service": service,
        "service_name": label,
        "details": details or "Customer sent a screenshot."
    }
    USER_TO_ORDER[uid] = oid

    kb = [
        [InlineKeyboardButton("👤 Claim", callback_data=f"claim_{oid}")],
        [
            InlineKeyboardButton("💰 Paid", callback_data=f"paid_{oid}"),
            InlineKeyboardButton("❌ Unpaid", callback_data=f"unpaid_{oid}"),
            InlineKeyboardButton("🔒 Close", callback_data=f"close_{oid}")
        ]
    ]

    await context.bot.send_message(
        ADMIN_CHAT_ID,
        f"🆕 NEW ORDER #{oid}\n\n"
        f"📂 Service: {label}\n\n"
        f"📋 Customer details:\n{ORDERS[oid]['details']}\n\n"
        "After claiming, use /price 125.50 to send the final price.",
        reply_markup=InlineKeyboardMarkup(kb)
    )

    if photo_id:
        await context.bot.send_photo(
            ADMIN_CHAT_ID,
            photo_id,
            caption=f"📎 Screenshot for order #{oid}"
        )

    await message.reply_text(
        f"⏳ Your request has been received as order #{oid}.\n\n"
        "An agent will review it and connect with you here."
    )
    context.user_data.clear()


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = update.message
    uid = m.from_user.id
    text = m.text or ""

    if uid in ADMIN_ACTIVE:
        order = ORDERS.get(ADMIN_ACTIVE[uid])
        if order and order["status"] != "CLOSED":
            await context.bot.send_message(
                order["user_id"], f"💬 Agent: {text}"
            )
        return

    if uid in USER_TO_ORDER:
        oid, order = active_order(uid)
        if order and order.get("admin") and order["status"] != "CLOSED":
            await context.bot.send_message(
                order["admin"], f"💬 Customer: {text}"
            )
            return
        if order and order["status"] != "CLOSED":
            await m.reply_text(
                f"Your request #{oid} is waiting for an agent. "
                "Your message has been received."
            )
            return

    if context.user_data.get("step") == "info":
        service = context.user_data.get("service", "unknown")
        details = f"Service: {SERVICES.get(service, service)}"

        if context.user_data.get("restaurant"):
            details += (
                f"\nRestaurant/category: {context.user_data['restaurant']}"
            )

        details += f"\nCustomer message/link: {text}"
        await create_order(m, context, details)
    else:
        await m.reply_text("Please choose a service with /start to begin.")


async def photo_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = update.message
    uid = m.from_user.id
    photo_id = m.photo[-1].file_id
    caption = m.caption or ""

    if uid in ADMIN_ACTIVE:
        order = ORDERS.get(ADMIN_ACTIVE[uid])
        if order and order["status"] != "CLOSED":
            await context.bot.send_photo(
                order["user_id"], photo_id, caption=caption or None
            )
        return

    if uid in USER_TO_ORDER:
        oid, order = active_order(uid)

        if order and order.get("admin") and order["status"] != "CLOSED":
            await context.bot.send_photo(
                order["admin"], photo_id, caption=caption or None
            )
            return

        if order and order["status"] != "CLOSED":
            await context.bot.send_photo(
                ADMIN_CHAT_ID,
                photo_id,
                caption=f"📎 Additional screenshot for order #{oid}"
            )
            await m.reply_text(
                f"Added your screenshot to order #{oid}. "
                "An agent will respond here."
            )
            return

    if context.user_data.get("step") == "info":
        service = context.user_data.get("service", "unknown")
        details = f"Service: {SERVICES.get(service, service)}"

        if context.user_data.get("restaurant"):
            details += (
                f"\nRestaurant/category: {context.user_data['restaurant']}"
            )

        if caption:
            details += f"\nCustomer caption: {caption}"

        await create_order(m, context, details, photo_id)
    else:
        await m.reply_text(
            "Please choose a service with /start first, then send your screenshot."
        )


async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global LIFETIME_SALES

    q = update.callback_query
    await q.answer()
    action, oid = q.data.split("_", 1)
    order = ORDERS.get(oid)

    if not order:
        await q.message.reply_text(
            "This order isn't available in the current bot session."
        )
        return

    if action == "claim":
        if order["status"] == "CLOSED":
            await q.message.reply_text(f"🔒 Order {oid} is already closed.")
            return

        if order.get("admin") and order["admin"] != q.from_user.id:
            await q.message.reply_text(
                f"Order {oid} has already been claimed."
            )
            return

        order["admin"] = q.from_user.id
        ADMIN_ACTIVE[q.from_user.id] = oid

        await context.bot.send_message(
            order["user_id"],
            "👤 An agent has joined the chat. You can now communicate "
            "privately with your agent through this bot."
        )
        await q.message.reply_text(
            f"👤 Order {oid} claimed. Use /price 125.50 to send a final price."
        )

    elif action == "paid":
        if order["status"] == "CLOSED":
            await q.message.reply_text(f"Order {oid} is closed.")
            return

        order["status"] = "PAID"

        if not order.get("sale_counted") and order.get("price") is not None:
            LIFETIME_SALES += order["price"]
            order["sale_counted"] = True

        amount = order.get("price") or 0.0
        await q.message.reply_text(
            f"✅ Order {oid} marked PAID\n💰 Price: ${amount:.2f}"
        )
        await context.bot.send_message(
            order["user_id"],
            f"✅ Your order #{oid} has been marked paid/completed.\n"
            f"💰 Total: ${amount:.2f}\n\n"
            "This chat stays open until the agent closes it."
        )

    elif action == "unpaid":
        if order["status"] != "CLOSED":
            order["status"] = "UNPAID"
        await q.message.reply_text(
            f"❌ Order {oid} marked UNPAID. Conversation remains open."
        )

    elif action == "close":
        order["status"] = "CLOSED"
        uid, aid = order["user_id"], order.get("admin")

        if USER_TO_ORDER.get(uid) == oid:
            USER_TO_ORDER.pop(uid, None)

        if aid and ADMIN_ACTIVE.get(aid) == oid:
            ADMIN_ACTIVE.pop(aid, None)

        await q.message.reply_text(
            f"🔒 Order {oid} closed. Private relay has been closed."
        )
        await context.bot.send_message(
            uid,
            "🔒 This order has been closed.\n\n"
            "Thank you for using Paradise Oasis Concierge."
        )


async def set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id

    if uid not in ADMIN_ACTIVE:
        await update.message.reply_text(
            "Claim an order first, then use /price 125.50."
        )
        return

    oid = ADMIN_ACTIVE[uid]
    order = ORDERS.get(oid)

    if not order or order["status"] == "CLOSED":
        await update.message.reply_text(
            "There is no open order attached to your agent chat."
        )
        return

    try:
        price = float(context.args[0])
        if price < 0 or price != price or price in (
            float("inf"), float("-inf")
        ):
            raise ValueError
    except (ValueError, IndexError):
        await update.message.reply_text(
            "Use the command like this:\n/price 125.50"
        )
        return

    order["price"] = round(price, 2)

    await update.message.reply_text(
        f"💰 Final price sent for order #{oid}: ${order['price']:.2f}\n"
        "The conversation remains open."
    )
    await context.bot.send_message(
        order["user_id"],
        f"💰 Final price for your order #{oid}: ${order['price']:.2f}\n\n"
        "Reply here if you have questions. This conversation remains open."
    )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is missing.")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("price", set_price))

    app.add_handler(
        CallbackQueryHandler(service_select, pattern=r"^svc_")
    )
    app.add_handler(
        CallbackQueryHandler(restaurant_select, pattern=r"^rest_")
    )
    app.add_handler(
        CallbackQueryHandler(back_main, pattern=r"^back_main$")
    )
    app.add_handler(
        CallbackQueryHandler(
            admin_actions, pattern=r"^(claim|paid|unpaid|close)_"
        )
    )

    app.add_handler(MessageHandler(filters.PHOTO, photo_router))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_router)
    )

    print("✅ Paradise Oasis Concierge running")
    app.run_polling()


if __name__ == "__main__":
    main()

