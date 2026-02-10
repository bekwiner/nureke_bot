from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from config import SUPERADMIN_IDS
from database import db, utc_now
import asyncio
from datetime import datetime, timedelta, timezone
import random
import string

from keyboards import prices_back_inline

from states import AdminMenuStates
from keyboards import admin_menu_keyboard, remove_keyboard

from states import AdminEditPricesStates
from keyboards import dynamic_packages_keyboard

from states import AdminPackagesStates
from keyboards import admin_packages_menu_keyboard

from keyboards import voucher_quantity_keyboard
from states import VoucherStates

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from states import AdminContactTextStates

from states import AdminOrdersStates
from keyboards import orders_back_keyboard

from keyboards import cancel_process_keyboard

from states import AdminUserSearchStates
from keyboards import user_search_back_keyboard

from states import AdminVouchersStates
from keyboards import admin_vouchers_menu_keyboard

from states import PromoCodeStates
from keyboards import promo_enter_keyboard

from states import AdminPromoStates
from keyboards import admin_promocode_menu_keyboard
from keyboards import back_only_keyboard
from keyboards import promo_input_cancel_keyboard

from keyboards import promocode_back_to_menu_keyboard
from keyboards import main_menu_text_back_keyboard

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from keyboards import (
    main_menu_keyboard,
    confirm_package_keyboard,
    admin_order_keyboard,
    admin_order_edit_keyboard,
    admin_order_edit_cancel_keyboard,
)
from states import (
    OrderStates,
    AdminStates,
    AdminOrderEditStates,
    WithdrawStates,
    WithdrawEdit,
    AdminBroadcastStates,
    AdminMainMenuPhotoStates,
    AdminRoleStates,
    AdminPaymentCardsStates,
    AdminLogChatStates,
    BonusCodeStates,
    AdminStatsStates,
    MainMenuTextEditState,
)
from keyboards import (
    bonus_code_menu_keyboard,
    bonus_code_buy_keyboard,
    admin_broadcast_menu_keyboard,
    broadcast_confirm_keyboard,
    admin_roles_menu_keyboard,
    admin_payment_cards_menu_keyboard,
    admin_logchat_menu_keyboard,
    admin_stats_admins_keyboard,
    admin_stats_detail_keyboard,
)

router = Router()

MAIN_MENU_TEXT = (
    "🎮 Free Fire uchun Almaz — ishonch bilan, tez va xotirjam.\n\n"

    "Bu yerda siz shunchaki almaz sotib olmaysiz —\n"
    "siz xavfsizlik, tezlik va halollikni tanlaysiz.\n\n"

    "⚡ O‘rtacha yetkazish: 5–15 daqiqa\n"  
    "🔒 Hisobingiz xavfsizligi — 1-o‘rinda\n"  
    "👮‍♂️ Adminlar real va onlayn\n"  
    "🎁 Bonuslar va sovg‘alar mavjud\n\n"

    "💬 Minglab foydalanuvchilar bizni tanlagan.\n"
    "Endi navbat sizda.\n\n"

    "👇 Boshlash uchun quyidan kerakli bo‘limni tanlang.\n"
)

ADMIN_ROLE_SUPER = "superadmin"
ADMIN_ROLE_MAIN = "main_admin"
ADMIN_ROLE_VIEWER = "viewer"

PERM_REVENUE_ROLES = (ADMIN_ROLE_SUPER, ADMIN_ROLE_MAIN)

ROLE_LABELS = {
    ADMIN_ROLE_SUPER: "SUPERADMIN",
    ADMIN_ROLE_MAIN: "MAIN ADMIN",
    ADMIN_ROLE_VIEWER: "VIEWER",
}

ADMIN_NAV_STACK_KEY = "nav_stack"


async def get_nav_stack(state: FSMContext) -> list[str]:
    data = await state.get_data()
    stack = data.get(ADMIN_NAV_STACK_KEY)
    return stack if isinstance(stack, list) else []


async def push_nav(state: FSMContext, key: str):
    stack = await get_nav_stack(state)
    if not stack or stack[-1] != key:
        stack.append(key)
    await state.update_data(**{ADMIN_NAV_STACK_KEY: stack})


async def pop_nav(state: FSMContext) -> str | None:
    stack = await get_nav_stack(state)
    if stack:
        stack.pop()
    await state.update_data(**{ADMIN_NAV_STACK_KEY: stack})
    return stack[-1] if stack else None


async def show_admin_menu(message: Message, state: FSMContext | None = None):
    if state is not None:
        await state.set_state(AdminMenuStates.menu)
    role = await get_admin_role(message.from_user.id)
    await message.answer(
        "🛠 ADMIN PANEL\n\nKerakli bo‘limni tanlang:",
        reply_markup=admin_menu_keyboard(role)
    )


async def show_admin_roles_menu(message: Message, state: FSMContext):
    rows = await db.fetch(
        "SELECT user_id, role, active FROM admins ORDER BY role, user_id"
    )
    text = "👮‍♂️ <b>ADMINLAR</b>\n\n"
    if not rows:
        text += "Hozircha adminlar yo‘q."
    else:
        for row in rows:
            r = row["role"]
            status = "🟢" if row["active"] else "🔴"
            text += f"{status} {row['user_id']} — {ROLE_LABELS.get(r, r)}\n"
    await state.set_state(AdminRoleStates.menu)
    await message.answer(text, reply_markup=admin_roles_menu_keyboard())


async def show_admin_promocode_menu(message: Message, state: FSMContext):
    await state.set_state(AdminPromoStates.menu)
    await message.answer("🎁 PROMOKODLAR BOSHQARUVI", reply_markup=admin_promocode_menu_keyboard())


async def show_admin_vouchers_menu(message: Message, state: FSMContext):
    await state.set_state(AdminVouchersStates.menu)
    await message.answer("💳 VOUCHERLAR BOSHQARUVI", reply_markup=admin_vouchers_menu_keyboard())


async def show_admin_packages_menu(message: Message, state: FSMContext):
    await state.set_state(AdminPackagesStates.menu)
    await message.answer("📦 PAKETLAR BOSHQARUVI", reply_markup=admin_packages_menu_keyboard())


async def show_admin_payment_cards_menu(message: Message, state: FSMContext):
    await state.set_state(AdminPaymentCardsStates.menu)
    rows = await list_payment_cards(active_only=False)
    text = "💳 <b>TO‘LOV KARTALARI</b>\n\n"
    if not rows:
        text += "Hozircha karta yo‘q."
    else:
        for row in rows:
            text += format_card_line(row) + "\n"
    await message.answer(text, reply_markup=admin_payment_cards_menu_keyboard())


async def render_admin_menu_by_key(message: Message, state: FSMContext, key: str | None):
    if key == "admin_roles":
        await show_admin_roles_menu(message, state)
        return
    if key == "admin_promocodes":
        await show_admin_promocode_menu(message, state)
        return
    if key == "admin_vouchers":
        await show_admin_vouchers_menu(message, state)
        return
    if key == "admin_packages":
        await show_admin_packages_menu(message, state)
        return
    if key == "admin_payment_cards":
        await show_admin_payment_cards_menu(message, state)
        return
    if key == "admin_orders":
        await admin_orders_menu(message, state)
        return
    await show_admin_menu(message, state)


def parse_role(text: str):
    if not text:
        return None
    t = text.strip().lower()
    if t in {"1", "superadmin", "owner", "super"}:
        return ADMIN_ROLE_SUPER
    if t in {"2", "main", "mainadmin", "main_admin", "main admin", "main-admin"}:
        return ADMIN_ROLE_MAIN
    if t in {"3", "viewer", "read", "read-only"}:
        return ADMIN_ROLE_VIEWER
    return None


def format_dt_utc5(dt_value) -> str:
    if not dt_value:
        return "-"
    if isinstance(dt_value, str):
        try:
            dt_value = datetime.fromisoformat(dt_value)
        except Exception:
            return str(dt_value)
    if dt_value.tzinfo is None:
        dt_value = dt_value.replace(tzinfo=timezone.utc)
    dt_utc5 = dt_value.astimezone(timezone(timedelta(hours=5)))
    return dt_utc5.strftime("%d.%m.%Y | %H:%M")


async def log_admin_action(admin_id: int, action: str, order_id: int = None, details: str = None):
    await db.execute(
        """
        INSERT INTO admin_logs (admin_id, action, order_id, details, created_at)
        VALUES ($1, $2, $3, $4, $5)
        """,
        admin_id,
        action,
        order_id,
        details,
        utc_now(),
    )


async def log_order_status_change(admin_id: int, order_id: int, old_status: str, new_status: str):
    details = f"STATUS {old_status} -> {new_status}"
    await log_admin_action(
        admin_id=admin_id,
        action="ORDER_STATUS_CHANGED",
        order_id=order_id,
        details=details,
    )


def admin_display_name(user) -> str:
    if getattr(user, "username", None):
        return f"@{user.username}"
    return user.full_name if getattr(user, "full_name", None) else str(user.id)


def mask_card_number(card_number: str) -> str:
    digits = "".join([c for c in (card_number or "") if c.isdigit()])
    if len(digits) < 8:
        return card_number
    return f"{digits[:4]} **** **** {digits[-4:]}"


def format_card_line(row) -> str:
    masked = mask_card_number(row["card_number"])
    parts = [f"🏦 {masked}"]
    if row.get("bank_name"):
        parts.append(f"{row['bank_name']}")
    if row.get("holder_name"):
        parts.append(f"{row['holder_name']}")
    active_mark = "✅" if row.get("active") else "⛔"
    return f"{active_mark} {' — '.join(parts)} (ID: {row['id']})"


async def list_payment_cards(active_only: bool = False):
    where = "WHERE active = TRUE" if active_only else ""
    return await db.fetch(
        f"""
        SELECT id, card_number, holder_name, bank_name, active, sort_order
        FROM payment_cards
        {where}
        ORDER BY active DESC, sort_order ASC, id ASC
        """
    )


async def get_log_setting(key: str, default: str = "") -> str:
    return (await get_setting(key, default)).strip()


async def is_log_enabled() -> bool:
    return (await get_log_setting("approved_channel_enabled", "false")).lower() in {"1", "true", "yes", "ha", "on"}


async def get_log_channel_username() -> str:
    return (await get_log_setting("approved_channel_username", "")).strip()


async def get_log_channel_chat_id():
    raw = await get_log_setting("approved_channel_chat_id", "")
    return int(raw) if raw.isdigit() else None


async def resolve_log_channel_id(bot):
    if not await is_log_enabled():
        return None, "Log o‘chirilgan."
    chat_id = await get_log_channel_chat_id()
    if chat_id:
        return chat_id, None
    username = await get_log_channel_username()
    if not username:
        return None, "Kanal username sozlanmagan."
    if not username.startswith("@"):
        username = f"@{username}"
    try:
        chat = await bot.get_chat(username)
        await set_setting("approved_channel_chat_id", str(chat.id))
        return chat.id, None
    except TelegramBadRequest:
        return None, "Kanal topilmadi. Username noto‘g‘ri yoki bot kanalga qo‘shilmagan."
    except TelegramForbiddenError:
        return None, "Bot kanalga yozolmayapti. Botni kanalga admin qilib qo‘ying."
    except Exception:
        return None, "Kanalni tekshirib bo‘lmadi."


async def mark_order_log_sent(order_id: int, status: str):
    await db.execute(
        """
        INSERT INTO order_log_notifications (order_id, status, sent_at)
        VALUES ($1, $2, $3)
        ON CONFLICT (order_id, status) DO NOTHING
        """,
        order_id,
        status,
        utc_now(),
    )


async def was_order_log_sent(order_id: int, status: str) -> bool:
    row = await db.fetchrow(
        "SELECT 1 FROM order_log_notifications WHERE order_id = $1 AND status = $2",
        order_id,
        status,
    )
    return row is not None


def order_type_label(order) -> str:
    t = (order.get("product_type") or "").lower()
    if t == "voucher":
        return "Voucher"
    if t == "almaz":
        return "Paket"
    return t or "Buyurtma"


async def send_order_log_if_needed(bot, order_id: int, status: str, status_label: str, admin_user):
    if status != "approved":
        return None
    if not await is_log_enabled():
        return None
    if await was_order_log_sent(order_id, status):
        return None

    order = await db.fetchrow(
        """
        SELECT id, user_id, username, first_name, product_type, product_name,
               almaz, quantity, price, ff_id, check_photo_id, updated_at, channel_posted_at
        FROM orders
        WHERE id = $1
        """,
        order_id,
    )
    if not order:
        return "Buyurtma topilmadi."
    if order["channel_posted_at"]:
        return None

    user_full = order["first_name"] or "Anonim"
    username = f"@{order['username']}" if order["username"] else "yo‘q"
    admin_name = admin_display_name(admin_user)
    time_str = format_dt_utc5(order["updated_at"])

    if (order["product_type"] or "").lower() == "voucher":
        product_block = (
            "💳 VOUCHER MA’LUMOTI\n"
            f"🎫 Nomi: {order['product_name']}\n"
            f"🧮 Soni: {order['quantity']} dona\n"
            f"💎 Jami almaz: {order['almaz']}\n"
            f"💰 Jami narx: {order['price']:,} so‘m\n"
            f"🎮 FF ID: {order['ff_id']}\n"
        )
    else:
        product_block = (
            "💎 PAKET MA’LUMOTI\n"
            f"📦 Paket: {order['product_name']}\n"
            f"💎 Almaz: {order['almaz']}\n"
            f"💰 Narx: {order['price']:,} so‘m\n"
            f"🎮 FF ID: {order['ff_id']}\n"
        )

    text = (
        "🧾 YANGI BUYURTMA\n"
        f"🧾 Buyurtma raqami: #{order['id']}\n"
        f"👤 Foydalanuvchi: {user_full}\n"
        f"🔗 Username: {username}\n"
        f"🆔 User ID: {order['user_id']}\n\n"
        f"{product_block}\n"
        f"📌 Holat: ✅ TASDIQLANDI\n"
        f"👮 Admin: {admin_name}\n"
        f"🕒 Sana: {time_str}"
    )

    try:
        channel_id, err = await resolve_log_channel_id(bot)
        if err:
            return err
        if order["check_photo_id"]:
            await bot.send_photo(channel_id, order["check_photo_id"], caption=text)
        else:
            await bot.send_message(channel_id, text)
        await mark_order_log_sent(order_id, status)
        await db.execute(
            "UPDATE orders SET channel_posted_at = $1 WHERE id = $2",
            utc_now(),
            order_id,
        )
        return None
    except TelegramBadRequest:
        print(f"LOG CHAT NOT FOUND order_id={order_id}")
        return "Log kanalga yuborilmadi: chat not found. Botni kanalga qo‘shing va admin qiling yoki username’ni tekshiring."
    except TelegramForbiddenError:
        print(f"LOG CHAT FORBIDDEN order_id={order_id}")
        return "Bot kanalga yozolmayapti. Botni kanalga admin qilib qo‘ying."
    except Exception as e:
        print(f"LOG SEND ERROR order_id={order_id} err={e}")
        return "Log kanalga yuborilmadi. Kanal sozlamasini tekshiring."


async def send_withdraw_log_if_needed(bot, request_id: int, admin_user):
    if not await is_log_enabled():
        return None

    req = await get_withdraw_request(request_id)
    if not req:
        return "So‘rov topilmadi."
    if req["status"] != "approved":
        return None
    if req["channel_posted_at"]:
        return None

    user = await get_user(req["user_id"])
    user_name = f"@{user['username']}" if user and user["username"] else f"{req['user_id']}"
    time_str = format_dt_utc5(req["processed_at"])
    text = (
        "✅ Tasdiqlandi\n\n"
        f"👤 User: {user_name}\n"
        f"💎 Miqdor: {req['amount']} Almaz\n"
        f"🎮 FF ID: {req['ff_id']}\n"
        f"🕒 Sana: {time_str}"
    )

    try:
        channel_id, err = await resolve_log_channel_id(bot)
        if err:
            return err
        await bot.send_message(channel_id, text)
        await db.execute(
            "UPDATE withdraw_requests SET channel_posted_at = $1 WHERE id = $2",
            utc_now(),
            request_id,
        )
        return None
    except TelegramBadRequest:
        print(f"LOG CHAT NOT FOUND withdraw_id={request_id}")
        return "Log kanalga yuborilmadi: chat not found. Botni kanalga qo‘shing va admin qiling yoki username’ni tekshiring."
    except TelegramForbiddenError:
        print(f"LOG CHAT FORBIDDEN withdraw_id={request_id}")
        return "Bot kanalga yozolmayapti. Botni kanalga admin qiling yoki kanal username noto‘g‘ri."
    except Exception as e:
        print(f"LOG SEND ERROR withdraw_id={request_id} err={e}")
        return "Log kanalga yuborilmadi. Kanal sozlamasini tekshiring."


async def get_user(user_id: int):
    return await db.fetchrow(
        """
        SELECT user_id, first_name, username, joined_at, almaz_balance, bonus_almaz, total_almaz
        FROM users
        WHERE user_id = $1
        """,
        user_id,
    )


async def add_almaz(user_id: int, amount: int):
    await db.execute(
        """
        UPDATE users
        SET almaz_balance = almaz_balance + $1
        WHERE user_id = $2
        """,
        amount,
        user_id,
    )


def resolve_proof_chat_id(value: str | None):
    if not value:
        return None
    v = value.strip()
    if not v:
        return None
    if v.startswith("@"):
        return v
    if v.isdigit():
        return int(v)
    return v


async def get_proof_channel_value() -> str | None:
    row = await db.fetchrow("SELECT value FROM settings WHERE key = $1", "withdraw_proof_channel")
    return row["value"] if row else None


async def create_withdraw_request(user_id: int, amount: int, ff_id: str) -> int:
    return await db.fetchval(
        """
        INSERT INTO withdraw_requests (user_id, amount, ff_id, status, created_at)
        VALUES ($1, $2, $3, 'pending', $4)
        RETURNING id
        """,
        user_id,
        amount,
        ff_id,
        utc_now(),
    )


async def get_withdraw_request(request_id: int):
    return await db.fetchrow(
        """
        SELECT id, user_id, amount, ff_id, status, created_at, processed_at, processed_by, note
        FROM withdraw_requests
        WHERE id = $1
        """,
        request_id,
    )


async def update_withdraw_status(request_id: int, status: str, processed_by: int | None, note: str | None):
    await db.execute(
        """
        UPDATE withdraw_requests
        SET status = $1,
            processed_at = $2,
            processed_by = $3,
            note = $4
        WHERE id = $5
        """,
        status,
        utc_now(),
        processed_by,
        note,
        request_id,
    )


async def add_withdraw_notification(request_id: int, admin_id: int, message_id: int):
    await db.execute(
        """
        INSERT INTO withdraw_notifications (request_id, admin_id, message_id, created_at)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (request_id, admin_id)
        DO UPDATE SET message_id = EXCLUDED.message_id, created_at = EXCLUDED.created_at
        """,
        request_id,
        admin_id,
        message_id,
        utc_now(),
    )


async def get_withdraw_notifications(request_id: int):
    rows = await db.fetch(
        """
        SELECT admin_id, message_id
        FROM withdraw_notifications
        WHERE request_id = $1
        """,
        request_id,
    )
    return [(r["admin_id"], r["message_id"]) for r in rows]


async def is_owner_or_admin(user_id: int) -> bool:
    if user_id in SUPERADMIN_IDS:
        return True
    role = await get_admin_role(user_id)
    return role in (ADMIN_ROLE_SUPER, ADMIN_ROLE_MAIN)


async def update_withdraw_admin_messages(bot, request_id: int, status_label: str):
    notifications = await get_withdraw_notifications(request_id)
    req = await get_withdraw_request(request_id)
    if not req:
        return
    user_id = req["user_id"]
    amount = req["amount"]
    ff_id = req["ff_id"]
    created_at = req["created_at"]
    processed_at = req["processed_at"]
    note = req["note"]

    user = await get_user(user_id)
    username = user["username"] if user else None
    almaz = user["almaz_balance"] if user else 0

    created_str = format_dt_utc5(created_at)
    processed_str = format_dt_utc5(processed_at) if processed_at else "—"
    note_part = f"\n📝 Izoh: {note}" if note else ""

    base_text = (
        "🧾 <b>Almaz yechish so'rovi</b>\n\n"
        f"👤 Foydalanuvchi: @{username or 'Anonim'} (ID: <code>{user_id}</code>)\n"
        f"💎 Joriy balans (so'rovdan keyingi holat bo'lishi mumkin): <b>{almaz} Almaz</b>\n"
        f"📥 Yechmoqchi bo'lgan miqdor: <b>{amount} Almaz</b>\n"
        f"🎮 Free Fire ID: <code>{ff_id}</code>\n"
        f"🕒 So'rov vaqti: {created_str}\n"
        f"🕒 Qayta ishlangan: {processed_str}"
        f"{note_part}\n\n"
        f"{status_label}"
    )

    for chat_id, message_id in notifications:
        try:
            await bot.edit_message_text(
                base_text,
                chat_id=chat_id,
                message_id=message_id,
                parse_mode="HTML"
            )
            await bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=None
            )
        except Exception:
            pass


async def send_proof_receipt(bot, request_id: int, user_id: int, amount: int, ff_id: str | None):
    channel_value = await get_proof_channel_value()
    chat_id = resolve_proof_chat_id(channel_value)
    if not chat_id:
        return

    user = await get_user(user_id)
    username = user["username"] if user else None
    mention = f"@{username}" if username else f"ID: {user_id}"
    ff_value = ff_id or "Ko'rsatilmagan"
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    text = (
        "✅ <b>Almaz yechish tasdiqlandi</b>\n\n"
        f"👤 Foydalanuvchi: {mention} (ID: <code>{user_id}</code>)\n"
        f"🎮 Free Fire ID: <code>{ff_value}</code>\n"
        f"💎 Miqdor: <b>{amount} Almaz</b>\n"
        f"🆔 So'rov ID: <code>{request_id}</code>\n"
        f"🕒 Tasdiqlangan vaqt: {now_str}"
    )

    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except Exception:
        pass


async def notify_admins_about_withdraw(bot, request_id: int):
    req = await get_withdraw_request(request_id)
    if not req:
        return
    user_id = req["user_id"]
    amount = req["amount"]
    ff_id = req["ff_id"]
    created_at = req["created_at"]

    user = await get_user(user_id)
    username = user["username"] if user else None
    almaz = user["almaz_balance"] if user else 0
    created_str = format_dt_utc5(created_at)

    text = (
        "🧾 <b>Yangi almaz yechish so'rovi</b>\n\n"
        f"👤 Foydalanuvchi: @{username or 'Anonim'} (ID: <code>{user_id}</code>)\n"
        f"💎 Joriy balans: <b>{almaz} Almaz</b>\n"
        f"📥 Yechmoqchi: <b>{amount} Almaz</b>\n"
        f"🎮 Free Fire ID: <code>{ff_id}</code>\n"
        f"🕒 So'rov vaqti: {created_str}\n\n"
        "Quyidagi tugmalar orqali so'rovni boshqaring 👇"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"wd_ok:{request_id}"),
                InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"wd_edit:{request_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"wd_reject:{request_id}"),
            ]
        ]
    )

    admin_ids = set(SUPERADMIN_IDS)
    extra_admins = await get_admins()
    for uid, role in extra_admins:
        if role in (ADMIN_ROLE_SUPER, ADMIN_ROLE_MAIN):
            admin_ids.add(uid)

    for chat_id in admin_ids:
        try:
            msg = await bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb)
            await add_withdraw_notification(request_id, chat_id, msg.message_id)
        except Exception:
            pass


async def save_admin_order_message(order_id: int, admin_id: int, message_id: int, caption: str):
    await db.execute(
        """
        INSERT INTO admin_order_messages (order_id, admin_id, message_id, caption, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (order_id, admin_id)
        DO UPDATE SET message_id = EXCLUDED.message_id, caption = EXCLUDED.caption, updated_at = EXCLUDED.updated_at
        """,
        order_id,
        admin_id,
        message_id,
        caption,
        utc_now(),
        utc_now(),
    )


async def update_admin_order_messages(bot, order_id: int, new_status_label: str, acting_admin_name: str, acting_admin_id: int):
    rows = await db.fetch(
        """
        SELECT admin_id, message_id, caption
        FROM admin_order_messages
        WHERE order_id = $1
        """,
        order_id,
    )
    if not rows:
        return
    now = utc_now()
    for row in rows:
        caption = row["caption"] or ""
        new_caption = update_order_status(caption, new_status_label)
        new_caption = append_admin_info(new_caption, acting_admin_name, acting_admin_id)
        try:
            await bot.edit_message_caption(
                chat_id=row["admin_id"],
                message_id=row["message_id"],
                caption=new_caption,
                reply_markup=None,
            )
        except Exception:
            pass
        await db.execute(
            """
            UPDATE admin_order_messages
            SET caption = $1, updated_at = $2
            WHERE order_id = $3 AND admin_id = $4
            """,
            new_caption,
            now,
            order_id,
            row["admin_id"],
        )


async def update_admin_order_field_messages(bot, order_id: int, field: str, value, acting_admin_name: str, acting_admin_id: int):
    rows = await db.fetch(
        """
        SELECT admin_id, message_id, caption
        FROM admin_order_messages
        WHERE order_id = $1
        """,
        order_id,
    )
    if not rows:
        return
    now = utc_now()
    for row in rows:
        caption = row["caption"] or ""
        if field == "almaz":
            new_line = f"💎 Almaz: {value}"
            if "💎 Jami almaz:" in caption:
                new_line = f"💎 Jami almaz: {value}"
                caption = replace_caption_line(caption, ["💎 Jami almaz:"], new_line)
            else:
                caption = replace_caption_line(caption, ["💎 Almaz:"], new_line)
        elif field == "price":
            new_line = f"💰 Narx: {format_money(value)} so‘m"
            if "💰 Jami narx:" in caption:
                new_line = f"💰 Jami narx: {format_money(value)} so‘m"
                caption = replace_caption_line(caption, ["💰 Jami narx:"], new_line)
            else:
                caption = replace_caption_line(caption, ["💰 Narx:"], new_line)
        elif field == "ff_id":
            caption = replace_caption_line(caption, ["🎮 FF ID:"], f"🎮 FF ID: {value}")
        elif field == "product_name":
            if "🎫 Nomi:" in caption:
                caption = replace_caption_line(caption, ["🎫 Nomi:"], f"🎫 Nomi: {value}")
            else:
                caption = replace_caption_line(caption, ["📦 Paket:"], f"📦 Paket: {value}")

        caption = append_admin_info(caption, acting_admin_name, acting_admin_id)
        try:
            await bot.edit_message_caption(
                chat_id=row["admin_id"],
                message_id=row["message_id"],
                caption=caption,
                reply_markup=None,
            )
        except Exception:
            pass
        await db.execute(
            """
            UPDATE admin_order_messages
            SET caption = $1, updated_at = $2
            WHERE order_id = $3 AND admin_id = $4
            """,
            caption,
            now,
            order_id,
            row["admin_id"],
        )


async def get_admin_role(user_id: int):
    row = await db.fetchrow(
        "SELECT role FROM admins WHERE user_id = $1 AND active = TRUE",
        user_id,
    )
    return row["role"] if row else None


async def get_admins():
    rows = await db.fetch(
        "SELECT user_id, role FROM admins WHERE active = TRUE"
    )
    return [(r["user_id"], r["role"]) for r in rows]


async def is_admin(user_id: int) -> bool:
    return await get_admin_role(user_id) is not None


async def require_role(message: Message, roles: tuple[str, ...]):
    role = await get_admin_role(message.from_user.id)
    if role not in roles:
        await message.answer("⛔ Sizda ruxsat yo‘q")
        return None
    return role


async def get_setting(key: str, default: str = "") -> str:
    row = await db.fetchrow("SELECT value FROM settings WHERE key = $1", key)
    return row["value"] if row else default


async def set_setting(key: str, value: str) -> None:
    await db.execute(
        """
        INSERT INTO settings (key, value)
        VALUES ($1, $2)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
        """,
        key,
        value,
    )


async def get_main_menu_text() -> str:
    text = (await get_setting("main_menu_text", "")).strip()
    return text if text else MAIN_MENU_TEXT


async def show_main_menu_message(message: Message, text: str | None = None):
    if not text:
        text = await get_main_menu_text()
    photo_id = (await get_setting("main_menu_photo_id")).strip()
    if photo_id:
        await message.answer_photo(photo_id, caption=text, reply_markup=main_menu_keyboard())
    else:
        await message.answer(text, reply_markup=main_menu_keyboard())


async def show_main_menu_callback(callback: CallbackQuery, text: str | None = None):
    if not text:
        text = await get_main_menu_text()
    photo_id = (await get_setting("main_menu_photo_id")).strip()
    if photo_id:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer_photo(photo_id, caption=text, reply_markup=main_menu_keyboard())
    else:
        await callback.message.edit_text(text, reply_markup=main_menu_keyboard())


async def safe_edit(callback: CallbackQuery, text: str, reply_markup=None, allow_photo: bool = False):
    msg = callback.message
    try:
        if msg.text is not None:
            await msg.edit_text(text, reply_markup=reply_markup)
            return
        if msg.caption is not None:
            if allow_photo:
                await msg.edit_caption(caption=text, reply_markup=reply_markup)
            else:
                try:
                    await msg.delete()
                except Exception:
                    pass
                await msg.answer(text, reply_markup=reply_markup)
            return
        await msg.answer(text, reply_markup=reply_markup)
    except Exception:
        await msg.answer(text, reply_markup=reply_markup)


def bonus_bp_for_use_count(use_count: int) -> int:
    if use_count <= 0:
        return 0
    if use_count == 1:
        return 300
    if use_count == 2:
        return 250
    if use_count == 3:
        return 250
    if 4 <= use_count <= 5:
        return 200
    return 100


async def get_bonus_use_state(code_id: int, user_id: int):
    row = await db.fetchrow(
        """
        SELECT id, use_count, cycle_start_at, last_used_at
        FROM bonus_code_uses
        WHERE code_id = $1 AND user_id = $2
        """,
        code_id,
        user_id,
    )
    now = utc_now()
    if not row:
        return {
            "row_id": None,
            "use_count": 0,
            "cycle_start_at": now,
            "reset": True,
        }

    cycle_start_at = row["cycle_start_at"] or row["last_used_at"] or now
    if cycle_start_at.tzinfo is None:
        cycle_start_at = cycle_start_at.replace(tzinfo=timezone.utc)

    if now - cycle_start_at >= timedelta(days=5):
        return {
            "row_id": row["id"],
            "use_count": 0,
            "cycle_start_at": now,
            "reset": True,
        }

    return {
        "row_id": row["id"],
        "use_count": row["use_count"] or 0,
        "cycle_start_at": cycle_start_at,
        "reset": False,
    }


async def get_active_bonus_code(user_id: int):
    now = utc_now()
    row = await db.fetchrow(
        """
        SELECT id, code, expires_at
        FROM bonus_codes
        WHERE owner_id = $1 AND active = TRUE
        """,
        user_id,
    )
    if not row:
        return None

    if row["expires_at"] and row["expires_at"] <= now:
        await db.execute(
            "UPDATE bonus_codes SET active = FALSE WHERE id = $1",
            row["id"],
        )
        return None

    return row


async def build_bonus_menu_text(user_id: int):
    base = (
        "🎁 Bonusli kod orqali donat — foydaliroq xarid.\n\n"
        "Bu bo‘limda siz:\n"
        "• o‘zingizga bonus kod yaratasiz\n"
        "• do‘stlaringiz bilan bo‘lishasiz\n"
        "• har bir xariddan bonus olasiz\n\n"
        "👇 Boshlash uchun quyidagi tugmalardan foydalaning."
    )

    return base



def build_bonus_code_card(code: str, expires_at) -> str:
    exp_text = format_dt_utc5(expires_at)
    return (
        "✅ <b>Sizda aktiv kod bor:</b>\n\n"
        f"🎁 Kod: <code>{code}</code>\n"
        f"⏳ Tugash: {exp_text}\n\n"
        "Kod tugagach yangisini yaratishingiz mumkin."
    )

def update_order_status(caption: str, new_status: str) -> str:
    if "📌 Holat:" in caption:
        lines = caption.split("\n")
        updated_lines = []

        for line in lines:
            if line.startswith("📌 Holat:"):
                updated_lines.append(f"📌 Holat: {new_status}")
            else:
                updated_lines.append(line)

        return "\n".join(updated_lines)

    # agar holat qatori bo‘lmasa (kam ehtimol)
    return caption + f"\n\n📌 Holat: {new_status}"


def append_admin_info(caption: str, admin_name: str, admin_id: int) -> str:
    admin_line = f"👮 Admin: {admin_name} ({admin_id})"
    if "👮 Admin:" in caption:
        lines = caption.split("\n")
        updated = []
        for line in lines:
            if line.startswith("👮 Admin:"):
                updated.append(admin_line)
            else:
                updated.append(line)
        return "\n".join(updated)

    return caption + f"\n{admin_line}"


def replace_caption_line(caption: str, prefixes: list[str], new_line: str) -> str:
    lines = caption.split("\n") if caption else []
    for i, line in enumerate(lines):
        for prefix in prefixes:
            if line.startswith(prefix):
                lines[i] = new_line
                return "\n".join(lines)
    lines.append(new_line)
    return "\n".join(lines)


def format_money(value: int) -> str:
    return f"{value:,}"


async def create_reminder(user_id: int, order_type: str):
    today = datetime.now().date()

    # 🛑 bugun allaqachon yuborilgan reminder bormi?
    row = await db.fetchrow(
        """
        SELECT id FROM reminders
        WHERE user_id = $1
          AND sent = TRUE
          AND date(send_at) = $2
        """,
        user_id,
        today,
    )
    if row:
        return  # 🚫 bugun yana yubormaymiz

    # 🛑 bugun kutilayotgan reminder bormi?
    row = await db.fetchrow(
        """
        SELECT id FROM reminders
        WHERE user_id = $1
          AND sent = FALSE
        """,
        user_id,
    )
    if row:
        return  # 🚫 allaqachon navbatda bor

    now = utc_now()
    send_time = now + timedelta(hours=6)  # ⏱ PRODUCTION

    await db.execute(
        """
        INSERT INTO reminders (user_id, type, created_at, send_at)
        VALUES ($1, $2, $3, $4)
        """,
        user_id,
        order_type,
        now,
        send_time,
    )

# ================= START =================
@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    print(f"/start from user_id={message.from_user.id} chat_id={message.chat.id} state={current_state}")

    await state.clear()
    user = message.from_user

    await db.execute(
        """
        INSERT INTO users (user_id, first_name, username, joined_at)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (user_id) DO NOTHING
        """,
        user.id,
        user.first_name,
        user.username,
        utc_now(),
    )

    role = await get_admin_role(user.id)
    await state.update_data(**{ADMIN_NAV_STACK_KEY: []})
    print(f"/start role_check user_id={user.id} role={role}")
    try:
        await show_main_menu_message(message)
    except Exception as e:
        print("START HANDLER SEND ERROR:", repr(e))



# ================= BONUS CODE MENU =================
@router.callback_query(F.data == "bonus_code_menu")
async def bonus_code_menu_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BonusCodeStates.menu)

    text = await build_bonus_menu_text(callback.from_user.id)
    await safe_edit(callback, text, reply_markup=bonus_code_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "bonus_code_create")
async def bonus_code_create_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BonusCodeStates.menu)
    user_id = callback.from_user.id
    now = utc_now()

    existing = await get_active_bonus_code(user_id)
    if existing:
        card_text = build_bonus_code_card(existing["code"], existing["expires_at"])
        back_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data="bonus_code_menu")]]
        )
        await safe_edit(callback, card_text, reply_markup=back_keyboard)
        await callback.answer()
        return

    code = None
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(10):
        candidate = "".join(random.choices(alphabet, k=random.randint(6, 8)))
        row = await db.fetchrow("SELECT 1 FROM bonus_codes WHERE code = $1", candidate)
        if not row:
            code = candidate
            break

    if not code:
        await callback.answer("❌ Kod yaratishda xato, qayta urinib ko‘ring", show_alert=True)
        return

    expires_at = now + timedelta(days=4)

    await db.execute(
        """
        INSERT INTO bonus_codes (code, owner_id, created_at, expires_at, active)
        VALUES ($1, $2, $3, $4, TRUE)
        """,
        code,
        user_id,
        now,
        expires_at,
    )

    card_text = build_bonus_code_card(code, expires_at)
    back_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Orqaga", callback_data="bonus_code_menu")]]
    )
    await safe_edit(callback, card_text, reply_markup=back_keyboard)
    await callback.answer()


@router.callback_query(F.data == "bonus_code_use")
async def bonus_code_use_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BonusCodeStates.waiting_code_input)

    back_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="bonus_code_menu")]
        ]
    )

    await safe_edit(
        callback,
        "🎁 <b>KODNI KIRITING</b>\n\n"
        "Masalan:\n"
        "<code>ZONIKS88</code>",
        reply_markup=back_keyboard,
    )
    await callback.answer()


@router.message(BonusCodeStates.waiting_code_input)
async def bonus_code_use_input(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    user_id = message.from_user.id
    now = utc_now()

    row = await db.fetchrow(
        """
        SELECT id, owner_id, expires_at, active
        FROM bonus_codes
        WHERE code = $1
        """,
        code,
    )

    if not row or not row["active"]:
        await message.answer("❌ Bunday kod mavjud emas yoki faol emas")
        return

    if row["expires_at"] and row["expires_at"] <= now:
        await db.execute(
            "UPDATE bonus_codes SET active = FALSE WHERE id = $1",
            row["id"],
        )
        await message.answer("⏰ Ushbu kod muddati tugagan")
        return

    if row["owner_id"] == user_id:
        await message.answer("⛔ Siz o‘zingiz yaratgan koddan foydalana olmaysiz")
        return

    await state.update_data(
        bonus_code_id=row["id"],
        bonus_owner_id=row["owner_id"],
        bonus_code=code,
    )
    await state.set_state(BonusCodeStates.menu)

    use_state = await get_bonus_use_state(row["id"], user_id)
    next_use_count = use_state["use_count"] + 1
    bonus_bp = bonus_bp_for_use_count(next_use_count)
    bonus_percent = bonus_bp / 100

    progress = f"{min(next_use_count, 5)}/5" if next_use_count <= 5 else "6+"

    text = (
        "✅ <b>KOD QABUL QILINDI!</b>\n\n"
        f"🔥 Joriy bonus: +{bonus_percent}%\n"
        f"📈 Progress: {progress}\n"
        f"🤝 Do‘stingiz ham +{bonus_percent}% oladi\n\n"
        "Endi paket yoki voucher tanlang:"
    )

    await message.answer(text, reply_markup=bonus_code_buy_keyboard())


@router.callback_query(F.data == "bonus_buy_almaz")
async def bonus_buy_almaz_handler(callback: CallbackQuery, state: FSMContext):
    await buy_almaz_handler(callback, state)


@router.callback_query(F.data == "bonus_buy_voucher")
async def bonus_buy_voucher_handler(callback: CallbackQuery, state: FSMContext):
    await buy_voucher_handler(callback, state)


# ================= BUY FLOW =================
@router.callback_query(F.data == "buy_almaz")
async def buy_almaz_handler(callback: CallbackQuery, state: FSMContext):
    rows = await db.fetch(
        "SELECT id, name, almaz, price FROM packages WHERE active = TRUE"
    )

    if not rows:
        await callback.answer("❌ Hozircha paketlar mavjud emas", show_alert=True)
        return

    packages = [
        {"id": r["id"], "name": r["name"], "almaz": r["almaz"], "price": r["price"]}
        for r in rows
    ]

    await state.set_state(OrderStates.choosing_package)

    await safe_edit(
        callback,
        "💎 Kerakli almaz paketini tanlang.\n\n"

        "⚡ Tez yetkazish • 🔒 Xavfsiz • 🎁 Bonuslar mavjud",
        reply_markup=dynamic_packages_keyboard(packages)
    )
    await callback.answer()



@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_main_menu_callback(callback)
    await callback.answer()




@router.callback_query(F.data == "back_to_packages")
async def back_to_packages_handler(callback: CallbackQuery, state: FSMContext):
    rows = await db.fetch(
        "SELECT id, name, almaz, price FROM packages WHERE active = TRUE"
    )

    if not rows:
        await callback.answer("❌ Paketlar yo‘q", show_alert=True)
        return

    packages = [
        {"id": r["id"], "name": r["name"], "almaz": r["almaz"], "price": r["price"]}
        for r in rows
    ]

    await state.set_state(OrderStates.choosing_package)

    await safe_edit(
        callback,
        "💎 Almaz paketini tanlang:",
        reply_markup=dynamic_packages_keyboard(packages)
    )
    await callback.answer()



# ================= PAYMENT =================
@router.callback_query(F.data == "go_to_payment")
async def go_to_payment_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OrderStates.waiting_ff_id)

    data = await state.get_data()

    await safe_edit(
        callback,
        "✅ <b>BUYURTMA MA’LUMOTI</b>\n\n"
        f"💎 Paket: {data.get('almaz')} 💎\n"
        f"💰 Narx: {data.get('price'):,} so‘m\n\n"
        "🆔 <b>Free Fire ID</b> raqamingizni kiriting:\n"
        "⚠️ <i>Diqqat: noto'g'ri ID jo'natilgan holatlarda Adminga murojaat qilishingiz kerak</i>"
    )
    await callback.answer()



@router.message(OrderStates.waiting_ff_id)
async def ff_id_handler(message: Message, state: FSMContext):
    ff_id = message.text.strip()

    if not ff_id.isdigit():
        await message.answer("❌ FF ID faqat raqamlardan iborat bo‘lishi kerak")
        return

    await state.update_data(ff_id=ff_id)
    await state.set_state(OrderStates.waiting_payment)

    active_cards = await list_payment_cards(active_only=True)
    if not active_cards:
        await message.answer(
            "❌ Hozircha to‘lov kartalari sozlanmagan.\n"
            "Iltimos, keyinroq urinib ko‘ring.",
            reply_markup=cancel_process_keyboard()
        )
        return

    cards_blocks = []
    for c in active_cards:
        title = (c.get("bank_name") or "Karta").strip()
        number = (c.get("card_number") or "").strip()
        holder = (c.get("holder_name") or "").strip()
        block_lines = [number]
        if holder:
            block_lines.append(holder)
        block = "<blockquote>" + "\n".join(block_lines) + "</blockquote>"
        cards_blocks.append(f"{title}:\n{block}")

    await message.answer(
        "💳 <b>TO‘LOV BOSQICHI</b>\n\n"
        "🏦 <b>Karta raqamlari:</b>\n\n"
        + "\n\n".join(cards_blocks)
        + "\n\n"
        "📌 <b>To‘lovni amalga oshiring</b> va\n"
        "🧾 <b>chekni rasm qilib</b> shu yerga yuboring.\n\n"
        "⚡ To‘lov tasdiqlangach, buyurtma tezkor ko‘rib chiqiladi.\n"
        "🔒 Jarayon xavfsiz va qo‘lda tekshiriladi.",
        reply_markup=cancel_process_keyboard(),
        parse_mode="HTML"
    )



@router.message(OrderStates.waiting_payment)
async def payment_handler(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer(
            "❌ Chek rasmini yuboring.\n"
            "📌 Iltimos, faqat BITTA rasm yuboring."
        )
        return

    data = await state.get_data()
    user = message.from_user
    photo_id = message.photo[-1].file_id

    # 🔹 BU YERDA INDENT TO‘G‘RI
    if data.get("is_voucher"):
        product_text = (
            "💳 <b>VOUCHER MA’LUMOTI</b>\n\n"
            f"🎫 Nomi: {data['name']}\n"
            f"🧮 Soni: {data['quantity']} dona\n"
            f"💎 Jami almaz: {data['total_almaz']}\n"
            f"💰 Jami narx: {data['total_price']:,} so‘m\n"
        )
    else:
        product_text = (
            "💎 <b>PAKET MA’LUMOTI</b>\n\n"
            f"📦 Paket: {data.get('package_name') or data.get('name')}\n"
            f"💎 Almaz: {data.get('almaz')}\n"
            f"💰 Narx: {data.get('price'):,} so‘m\n"
        )




    # ================= CREATE ORDER =================

    now = utc_now()
    bonus_code_id = data.get("bonus_code_id")
    bonus_owner_id = data.get("bonus_owner_id")

    order_id = await db.fetchval(
        """
        INSERT INTO orders (
            user_id,
            username,
            first_name,
            product_type,
            product_name,
            almaz,
            quantity,
            price,
            ff_id,
            check_photo_id,
            status,
            bonus_code_id,
            bonus_owner_id,
            bonus_percent_bp,
            bonus_amount,
            created_at,
            updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
        RETURNING id
        """,
        user.id,
        user.username,
        user.first_name,
        "voucher" if data.get("is_voucher") else "almaz",
        data.get("name") or data.get("package_name"),
        data.get("total_almaz", data.get("almaz")),
        data.get("quantity", 1),
        data.get("total_price", data.get("price")),
        data.get("ff_id"),
        photo_id,
        "pending",
        bonus_code_id,
        bonus_owner_id,
        0,
        0,
        now,
        now,
    )

    bonus_line = ""
    if bonus_code_id:
        bonus_line = f"🎁 Bonus kod: <code>{data.get('bonus_code', '')}</code>\n"

    admin_text = (
        "🧾 YANGI BUYURTMA\n\n"
        f"🧾 Buyurtma raqami: #{order_id}\n"
        f"👤 Foydalanuvchi: {user.full_name}\n"
        f"🔗 Username: @{user.username if user.username else 'yo‘q'}\n"
        f"🆔 User ID: {user.id}\n\n"
        f"{product_text}"
        f"🎮 FF ID: {data.get('ff_id')}\n\n"
        f"{bonus_line}"
        "📌 Holat: ⏳ Kutilmoqda"
    )
    admins = await get_admins()
    for admin_id, role in admins:
        reply_markup = None
        if role in (ADMIN_ROLE_SUPER, ADMIN_ROLE_MAIN):
            reply_markup = admin_order_keyboard(
                user.id,
                data.get("total_almaz", data.get("almaz")),
                order_id
            )
        try:
            sent = await message.bot.send_photo(
                chat_id=admin_id,
                photo=photo_id,
                caption=admin_text,
                reply_markup=reply_markup
            )
        except TelegramBadRequest as e:
            print(f"ADMIN SEND_PHOTO FAILED order_id={order_id} admin_id={admin_id} err={e}")
            continue
        except TelegramForbiddenError as e:
            print(f"ADMIN SEND_PHOTO FORBIDDEN order_id={order_id} admin_id={admin_id} err={e}")
            continue
        except Exception as e:
            print(f"ADMIN SEND_PHOTO ERROR order_id={order_id} admin_id={admin_id} err={e}")
            continue
        try:
            await save_admin_order_message(
                order_id=order_id,
                admin_id=admin_id,
                message_id=sent.message_id,
                caption=admin_text,
            )
        except Exception:
            pass

    await state.clear()

    await message.answer(
        "✅ To‘lov qabul qilindi!\n\n"
        f"🧾 Buyurtma raqami: #{order_id}\n"
        "⏱️ Tez orada admin tekshiradi."
    )

@router.callback_query(F.data.startswith("admin_confirm:"))
async def admin_confirm_handler(callback: CallbackQuery):
    role = await get_admin_role(callback.from_user.id)
    if role not in (ADMIN_ROLE_SUPER, ADMIN_ROLE_MAIN):
        await callback.answer("⛔ Sizda ruxsat yo‘q", show_alert=True)
        return

    try:
        _, order_id, user_id, almaz = callback.data.split(":")
        order_id = int(order_id)
        user_id = int(user_id)
        almaz = int(almaz)
    except Exception:
        await callback.answer("❌ Ma’lumot xato", show_alert=True)
        return

    order = await db.fetchrow(
        """
        SELECT id, almaz, status, bonus_code_id, bonus_owner_id
        FROM orders
        WHERE id = $1
        """,
        order_id,
    )
    if not order:
        await callback.answer("❌ Buyurtma topilmadi", show_alert=True)
        return
    if order["status"] != "pending":
        await callback.answer("⚠️ Buyurtma allaqachon ko‘rib chiqilgan", show_alert=True)
        return

    order_almaz = order["almaz"] or almaz
    now = utc_now()

    bonus_bp = 100
    bonus_amount = order_almaz * bonus_bp // 10000

    if order["bonus_code_id"]:
        use_state = await get_bonus_use_state(order["bonus_code_id"], user_id)
        next_use_count = use_state["use_count"] + 1
        bonus_bp = bonus_bp_for_use_count(next_use_count)
        bonus_amount = order_almaz * bonus_bp // 10000

        if use_state["row_id"]:
            await db.execute(
                """
                UPDATE bonus_code_uses
                SET use_count = $1, cycle_start_at = $2, last_used_at = $3
                WHERE id = $4
                """,
                next_use_count,
                use_state["cycle_start_at"],
                now,
                use_state["row_id"],
            )
        else:
            await db.execute(
                """
                INSERT INTO bonus_code_uses (code_id, user_id, use_count, cycle_start_at, last_used_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                order["bonus_code_id"],
                user_id,
                next_use_count,
                use_state["cycle_start_at"],
                now,
            )

        await db.execute(
            """
            UPDATE bonus_codes
            SET total_uses = total_uses + 1,
                total_bonus = total_bonus + $1
            WHERE id = $2
            """,
            bonus_amount,
            order["bonus_code_id"],
        )

        if order["bonus_owner_id"]:
            await db.execute(
                """
                UPDATE users
                SET
                    almaz_balance = almaz_balance + $1,
                    bonus_almaz = bonus_almaz + $1
                WHERE user_id = $2
                """,
                bonus_amount,
                order["bonus_owner_id"],
            )

    # bot bonus balansi
    bot_balance = int(await get_setting("bot_bonus_balance", "0") or 0)
    await set_setting("bot_bonus_balance", str(bot_balance + bonus_amount))

    # 💎 BUYER BALANCE UPDATE
    # xarid almazi balansga tushmaydi, faqat bonus tushadi
    await db.execute(
        """
        UPDATE users
        SET 
            almaz_balance = almaz_balance + $1,
            bonus_almaz = bonus_almaz + $1,
            total_almaz = total_almaz + $2
        WHERE user_id = $3
        """,
        bonus_amount,
        order_almaz,
        user_id,
    )

    # 🧾 ORDER STATUS UPDATE
    await db.execute(
        """
        UPDATE orders
        SET status = $1,
            admin_id = $2,
            updated_at = $3,
            approved_at = $4,
            bonus_percent_bp = $5,
            bonus_amount = $6
        WHERE id = $7
        """,
        "approved",
        callback.from_user.id,
        now,
        now,
        bonus_bp,
        bonus_amount,
        order_id,
    )

    # 🪵 ADMIN LOG
    await log_admin_action(
        admin_id=callback.from_user.id,
        action="ORDER_APPROVED",
        order_id=order_id,
        details=f"{order_almaz} almaz tasdiqlandi"
    )
    await log_order_status_change(
        admin_id=callback.from_user.id,
        order_id=order_id,
        old_status="pending",
        new_status="approved",
    )

    # 🧾 UPDATE ADMIN MESSAGE
    old_caption = callback.message.caption or ""
    new_caption = update_order_status(old_caption, "✅ TASDIQLANDI")
    new_caption = append_admin_info(
        new_caption,
        admin_display_name(callback.from_user),
        callback.from_user.id
    )

    await callback.message.edit_caption(
        caption=new_caption,
        reply_markup=None
    )
    await update_admin_order_messages(
        bot=callback.bot,
        order_id=order_id,
        new_status_label="✅ TASDIQLANDI",
        acting_admin_name=admin_display_name(callback.from_user),
        acting_admin_id=callback.from_user.id,
    )

    # 📩 USER NOTIFY
    try:
        menu_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="back_to_menu")]]
        )
        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                "🎉 <b>BUYURTMA TASDIQLANDI!</b>\n\n"
                f"💎 Almaz: {order_almaz}\n"
                f"🎁 Bonus: +{bonus_amount} 💎\n\n"
                "🙏 Xaridingiz uchun rahmat!"
            ),
            reply_markup=menu_kb
        )
    except Exception:
        pass

    log_err = await send_order_log_if_needed(
        callback.bot,
        order_id=order_id,
        status="approved",
        status_label="Tasdiqlandi",
        admin_user=callback.from_user,
    )
    if log_err:
        await callback.message.answer(f"⚠️ {log_err}")

    await callback.answer("✅ Buyurtma tasdiqlandi")


@router.callback_query(F.data.startswith("admin_fake:"))
async def admin_fake_handler(callback: CallbackQuery):
    role = await get_admin_role(callback.from_user.id)
    if role not in (ADMIN_ROLE_SUPER, ADMIN_ROLE_MAIN):
        await callback.answer("⛔ Sizda ruxsat yo‘q", show_alert=True)
        return

    _, order_id, user_id = callback.data.split(":")
    order_id = int(order_id)
    user_id = int(user_id)

    order = await db.fetchrow(
        "SELECT status FROM orders WHERE id = $1",
        order_id,
    )
    if not order:
        await callback.answer("❌ Buyurtma topilmadi", show_alert=True)
        return
    if order["status"] != "pending":
        await callback.answer("⚠️ Buyurtma allaqachon ko‘rib chiqilgan", show_alert=True)
        return

    await db.execute(
        """
        UPDATE orders
        SET status = $1,
            admin_id = $2,
            updated_at = $3,
            rejected_at = $4
        WHERE id = $5
        """,
        "rejected",
        callback.from_user.id,
        utc_now(),
        utc_now(),
        order_id,
    )

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="ORDER_REJECTED",
        order_id=order_id,
        details="Soxta chek deb belgilandi"
    )
    await log_order_status_change(
        admin_id=callback.from_user.id,
        order_id=order_id,
        old_status="pending",
        new_status="rejected",
    )

    old_caption = callback.message.caption or ""
    new_caption = update_order_status(old_caption, "❌ SOXTA CHEK")
    new_caption = append_admin_info(
        new_caption,
        admin_display_name(callback.from_user),
        callback.from_user.id
    )

    await callback.message.edit_caption(
        caption=new_caption,
        reply_markup=None
    )
    await update_admin_order_messages(
        bot=callback.bot,
        order_id=order_id,
        new_status_label="❌ SOXTA CHEK",
        acting_admin_name=admin_display_name(callback.from_user),
        acting_admin_id=callback.from_user.id,
    )

    await callback.bot.send_message(
        chat_id=user_id,
        text="❌ To‘lov rad etildi.\n🧾 Chek soxta yoki noto‘g‘ri.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="back_to_menu")]]
        )
    )

    # Kanal logi faqat tasdiqlanganlarda yuboriladi

    await callback.answer("Soxta chek")


@router.callback_query(F.data.startswith("admin_edit:"))
async def admin_edit_handler(callback: CallbackQuery, state: FSMContext):
    role = await get_admin_role(callback.from_user.id)
    if role not in (ADMIN_ROLE_SUPER, ADMIN_ROLE_MAIN):
        await callback.answer("⛔ Sizda ruxsat yo‘q", show_alert=True)
        return

    try:
        _, order_id, user_id = callback.data.split(":")
        order_id = int(order_id)
        user_id = int(user_id)
    except Exception:
        await callback.answer("❌ Ma’lumot xato", show_alert=True)
        return

    order = await db.fetchrow(
        "SELECT status FROM orders WHERE id = $1",
        order_id,
    )
    if not order:
        await callback.answer("❌ Buyurtma topilmadi", show_alert=True)
        return
    if order["status"] != "pending":
        await callback.answer("⚠️ Buyurtma allaqachon ko‘rib chiqilgan", show_alert=True)
        return

    await db.execute(
        """
        UPDATE orders
        SET status = $1,
            admin_id = $2,
            updated_at = $3
        WHERE id = $4
        """,
        "edited",
        callback.from_user.id,
        utc_now(),
        order_id,
    )
    await log_admin_action(
        admin_id=callback.from_user.id,
        action="ORDER_EDITED",
        order_id=order_id,
        details="Admin tahriri boshlandi"
    )
    await log_order_status_change(
        admin_id=callback.from_user.id,
        order_id=order_id,
        old_status="pending",
        new_status="edited",
    )

    old_caption = callback.message.caption or ""
    new_caption = update_order_status(old_caption, "✍️ ADMIN TAHRIRI")
    new_caption = append_admin_info(
        new_caption,
        admin_display_name(callback.from_user),
        callback.from_user.id
    )

    await callback.message.edit_caption(
        caption=new_caption,
        reply_markup=None
    )
    await update_admin_order_messages(
        bot=callback.bot,
        order_id=order_id,
        new_status_label="✍️ ADMIN TAHRIRI",
        acting_admin_name=admin_display_name(callback.from_user),
        acting_admin_id=callback.from_user.id,
    )

    # Kanal logi faqat tasdiqlanganlarda yuboriladi

    await state.set_state(AdminOrderEditStates.select_field)
    await state.update_data(target_user_id=user_id, target_order_id=order_id)

    await callback.message.answer(
        "✍️ Qaysi maydonni tahrirlaysiz?",
        reply_markup=admin_order_edit_keyboard(order_id, user_id),
    )
    await callback.answer("Tahrirlash")



@router.message(AdminStates.waiting_custom_message)
async def admin_custom_message_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data["target_user_id"]

    await message.bot.send_message(
        chat_id=user_id,
        text=message.text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="back_to_menu")]]
        )
    )

    # 🪵 ADMIN LOG
    await log_admin_action(
        admin_id=message.from_user.id,
        action="ADMIN_MESSAGE_SENT",
        details=f"User {user_id} ga xabar yuborildi"
    )

    await state.clear()
    await message.answer("✅ Xabar foydalanuvchiga yuborildi")


@router.callback_query(F.data.startswith("admin_edit_field:"))
async def admin_edit_field_handler(callback: CallbackQuery, state: FSMContext):
    role = await get_admin_role(callback.from_user.id)
    if role not in (ADMIN_ROLE_SUPER, ADMIN_ROLE_MAIN):
        await callback.answer("⛔ Sizda ruxsat yo‘q", show_alert=True)
        return

    try:
        _, order_id, user_id, field = callback.data.split(":")
        order_id = int(order_id)
        user_id = int(user_id)
    except Exception:
        await callback.answer("❌ Ma’lumot xato", show_alert=True)
        return

    await state.set_state(AdminOrderEditStates.edit_value)
    await state.update_data(target_order_id=order_id, target_user_id=user_id, edit_field=field)

    field_label = {
        "almaz": "Almaz",
        "price": "Narx",
        "ff_id": "FF ID",
        "product_name": "Nomi",
    }.get(field, "Qiymat")

    await callback.message.answer(
        f"✍️ {field_label} uchun yangi qiymatni kiriting:",
        reply_markup=admin_order_edit_cancel_keyboard(order_id, user_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_edit_cancel:"))
async def admin_edit_cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Bekor qilindi")


@router.message(AdminOrderEditStates.edit_value)
async def admin_edit_value_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("target_order_id")
    user_id = data.get("target_user_id")
    field = data.get("edit_field")

    if not order_id or not field:
        await state.clear()
        await message.answer("❌ Holat xato, qayta urinib ko‘ring.")
        return

    order = await db.fetchrow(
        "SELECT id, product_type, product_name, almaz, price, ff_id FROM orders WHERE id = $1",
        order_id,
    )
    if not order:
        await state.clear()
        await message.answer("❌ Buyurtma topilmadi.")
        return

    new_value_raw = (message.text or "").strip()
    if field in ("almaz", "price"):
        if not new_value_raw.isdigit():
            await message.answer("❌ Faqat raqam kiriting.")
            return
        new_value = int(new_value_raw)
    else:
        if not new_value_raw:
            await message.answer("❌ Bo‘sh qiymat bo‘lmaydi.")
            return
        new_value = new_value_raw

    column_map = {
        "almaz": "almaz",
        "price": "price",
        "ff_id": "ff_id",
        "product_name": "product_name",
    }
    column = column_map.get(field)
    if not column:
        await state.clear()
        await message.answer("❌ Noto‘g‘ri maydon.")
        return

    await db.execute(
        f"""
        UPDATE orders
        SET {column} = $1,
            updated_at = $2,
            admin_id = $3
        WHERE id = $4
        """,
        new_value,
        utc_now(),
        message.from_user.id,
        order_id,
    )

    await log_admin_action(
        admin_id=message.from_user.id,
        action="ORDER_FIELD_UPDATED",
        order_id=order_id,
        details=f"{column} updated"
    )

    await update_admin_order_field_messages(
        bot=message.bot,
        order_id=order_id,
        field=field,
        value=new_value,
        acting_admin_name=admin_display_name(message.from_user),
        acting_admin_id=message.from_user.id,
    )

    await state.set_state(AdminOrderEditStates.select_field)
    await message.answer(
        "✅ Saqlandi. Yana qaysi maydonni tahrirlaysiz?",
        reply_markup=admin_order_edit_keyboard(order_id, user_id),
    )


@router.message(Command("admin"))
async def admin_panel_handler(message: Message, state: FSMContext):
    role = await get_admin_role(message.from_user.id)
    if not role:
        await message.answer(
            "⛔ Sizda ruxsat yo‘q",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="back_to_menu")]]
            )
        )
        return

    await state.set_state(AdminMenuStates.menu)
    await state.update_data(**{ADMIN_NAV_STACK_KEY: []})
    await push_nav(state, "admin_menu")
    await show_admin_menu(message, state)


@router.message(Command("help"))
async def help_handler(message: Message):
    text = (
        "❓ <b>Yordam / FAQ</b>\n\n"
        "• Almaz yoki voucher sotib olish uchun menyudan kerakli bo‘limni tanlang.\n"
        "• To‘lovdan keyin chek rasmini yuboring.\n"
        "• Buyurtma tez orada adminlar tomonidan ko‘rib chiqiladi.\n"
        "• Savollar bo‘lsa, admin bilan bog‘lanish bo‘limidan foydalaning.\n\n"
        "⬇️ Asosiy menyuga qaytish uchun quyidagi tugmani bosing."
    )
    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🏠 Asosiy Menyu", callback_data="back_to_menu")]]
        )
    )

@router.message(AdminMenuStates.menu, F.text == "👥 Foydalanuvchilar soni")
async def users_stats_menu_handler(message: Message):
    role = await require_role(message, (ADMIN_ROLE_SUPER, ADMIN_ROLE_MAIN, ADMIN_ROLE_VIEWER))
    if not role:
        return

    now = utc_now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    total = await db.fetchval("SELECT COUNT(*) FROM users")

    today_count = await db.fetchval(
        "SELECT COUNT(*) FROM users WHERE date(joined_at) = $1",
        today,
    )

    week_count = await db.fetchval(
        "SELECT COUNT(*) FROM users WHERE joined_at >= $1",
        week_ago,
    )

    month_count = await db.fetchval(
        "SELECT COUNT(*) FROM users WHERE joined_at >= $1",
        month_ago,
    )

    await message.answer(
        "📊 FOYDALANUVCHILAR STATISTIKASI\n\n"
        f"👥 Umumiy: {total}\n"
        f"📅 Bugun: {today_count}\n"
        f"🗓 7 kun: {week_count}\n"
        f"🗓 30 kun: {month_count}"
    )

@router.message(AdminMenuStates.menu, F.text == "⬅️ Orqaga")
async def admin_back_handler(message: Message, state: FSMContext):
    await state.clear()
    await show_main_menu_message(message)


@router.message(AdminMenuStates.menu, F.text == "🖼 Asosiy menyu rasmi")
async def admin_main_menu_photo_start(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    await state.set_state(AdminMainMenuPhotoStates.waiting_photo)
    await message.answer(
        "🖼 Asosiy menyu uchun RASM yuboring.\n\n"
        "O‘chirish uchun: 0 yuboring.\n"
        "Orqaga qaytish uchun: ⬅️ Orqaga"
    )


@router.message(AdminMainMenuPhotoStates.waiting_photo)
async def admin_main_menu_photo_save(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    if message.text and message.text.strip() == "⬅️ Orqaga":
        await state.set_state(AdminMenuStates.menu)
        await message.answer(
            "🛠 ADMIN PANEL",
            reply_markup=admin_menu_keyboard(role),
        )
        return

    if message.text and message.text.strip() == "0":
        await set_setting("main_menu_photo_id", "")
        await state.set_state(AdminMenuStates.menu)
        await message.answer(
            "✅ Asosiy menyu rasmi o‘chirildi",
            reply_markup=admin_menu_keyboard(role),
        )
        return

    if not message.photo:
        await message.answer("❌ Iltimos, rasm yuboring yoki 0 yozing")
        return

    photo_id = message.photo[-1].file_id
    await set_setting("main_menu_photo_id", photo_id)

    await state.set_state(AdminMenuStates.menu)
    await message.answer(
        "✅ Asosiy menyu rasmi saqlandi",
        reply_markup=admin_menu_keyboard(role),
    )


@router.message(AdminMenuStates.menu, F.text == "📣 Reklama / Xabar")
async def admin_broadcast_menu(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    await state.set_state(AdminBroadcastStates.menu)
    await message.answer(
        "📣 <b>REKLAMA / XABAR</b>\n\nTurini tanlang:",
        reply_markup=admin_broadcast_menu_keyboard()
    )


@router.message(AdminBroadcastStates.menu)
async def admin_broadcast_type(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    if message.text == "⬅️ Orqaga":
        await state.set_state(AdminMenuStates.menu)
        await message.answer(
            "🛠 ADMIN PANEL",
            reply_markup=admin_menu_keyboard(role)
        )
        return

    type_map = {
        "📝 Matn": "text",
        "🖼 Rasm": "photo",
        "🎥 Video": "video",
        "🎵 Musiqa": "audio",
        "📎 Fayl": "document",
        "📊 So‘rovnoma": "poll",
    }
    broadcast_type = type_map.get(message.text)
    if not broadcast_type:
        await message.answer("❌ Noto‘g‘ri tur. Tugmalardan tanlang.")
        return

    await state.update_data(broadcast_type=broadcast_type)
    await state.set_state(AdminBroadcastStates.waiting_content)

    await message.answer(
        "📤 Endi kontentni yuboring:",
        reply_markup=remove_keyboard()
    )


@router.message(AdminBroadcastStates.waiting_content)
async def admin_broadcast_content(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    data = await state.get_data()
    b_type = data.get("broadcast_type")

    payload = {"type": b_type}

    if b_type == "text":
        if not message.text:
            await message.answer("❌ Matn yuboring.")
            return
        payload["text"] = message.text
        await message.answer("📌 Oldindan ko‘rish:\n\n" + message.text)

    elif b_type == "photo":
        if not message.photo:
            await message.answer("❌ Rasm yuboring.")
            return
        payload["file_id"] = message.photo[-1].file_id
        payload["caption"] = message.caption or ""
        await message.answer_photo(payload["file_id"], caption=payload["caption"])

    elif b_type == "video":
        if not message.video:
            await message.answer("❌ Video yuboring.")
            return
        payload["file_id"] = message.video.file_id
        payload["caption"] = message.caption or ""
        await message.answer_video(payload["file_id"], caption=payload["caption"])

    elif b_type == "audio":
        if not message.audio:
            await message.answer("❌ Musiqa (audio) yuboring.")
            return
        payload["file_id"] = message.audio.file_id
        payload["caption"] = message.caption or ""
        await message.answer_audio(payload["file_id"], caption=payload["caption"])

    elif b_type == "document":
        if not message.document:
            await message.answer("❌ Fayl yuboring.")
            return
        payload["file_id"] = message.document.file_id
        payload["caption"] = message.caption or ""
        await message.answer_document(payload["file_id"], caption=payload["caption"])

    elif b_type == "poll":
        if not message.poll:
            await message.answer("❌ So‘rovnoma yuboring.")
            return
        poll = message.poll
        payload["question"] = poll.question
        payload["options"] = [o.text for o in poll.options]
        payload["is_anonymous"] = poll.is_anonymous
        payload["allows_multiple_answers"] = poll.allows_multiple_answers
        await message.bot.send_poll(
            chat_id=message.from_user.id,
            question=poll.question,
            options=payload["options"],
            is_anonymous=poll.is_anonymous,
            allows_multiple_answers=poll.allows_multiple_answers,
        )

    else:
        await message.answer("❌ Noma’lum tur.")
        return

    await state.update_data(broadcast_payload=payload)
    await state.set_state(AdminBroadcastStates.confirm)

    await message.answer(
        "✅ Hammasi tayyor. Yuboramizmi?",
        reply_markup=broadcast_confirm_keyboard()
    )


@router.callback_query(F.data == "broadcast_cancel")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    role = await get_admin_role(callback.from_user.id)
    await callback.message.answer(
        "❌ Yuborish bekor qilindi",
        reply_markup=admin_menu_keyboard(role)
    )
    await callback.answer()


@router.callback_query(F.data == "broadcast_send")
async def broadcast_send(callback: CallbackQuery, state: FSMContext):
    role = await get_admin_role(callback.from_user.id)
    if role != ADMIN_ROLE_SUPER:
        await callback.answer("⛔ Sizda ruxsat yo‘q", show_alert=True)
        return

    data = await state.get_data()
    payload = data.get("broadcast_payload")

    if not payload:
        await callback.answer("❌ Kontent topilmadi", show_alert=True)
        return

    users = await db.fetch("SELECT user_id FROM users")
    sent = 0
    failed = 0

    for row in users:
        uid = row["user_id"]
        try:
            if payload["type"] == "text":
                await callback.bot.send_message(uid, payload["text"])
            elif payload["type"] == "photo":
                await callback.bot.send_photo(uid, payload["file_id"], caption=payload.get("caption", ""))
            elif payload["type"] == "video":
                await callback.bot.send_video(uid, payload["file_id"], caption=payload.get("caption", ""))
            elif payload["type"] == "audio":
                await callback.bot.send_audio(uid, payload["file_id"], caption=payload.get("caption", ""))
            elif payload["type"] == "document":
                await callback.bot.send_document(uid, payload["file_id"], caption=payload.get("caption", ""))
            elif payload["type"] == "poll":
                await callback.bot.send_poll(
                    chat_id=uid,
                    question=payload["question"],
                    options=payload["options"],
                    is_anonymous=payload.get("is_anonymous", True),
                    allows_multiple_answers=payload.get("allows_multiple_answers", False),
                )
            else:
                continue
            sent += 1
            await asyncio.sleep(0.03)
        except Exception:
            failed += 1

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="BROADCAST_SENT",
        details=f"type={payload['type']} sent={sent} failed={failed}"
    )

    await state.clear()
    await callback.message.answer(
        f"✅ Reklama yuborildi.\n\n"
        f"📨 Yuborildi: {sent}\n"
        f"⚠️ Xatolik: {failed}",
        reply_markup=admin_menu_keyboard(role)
    )
    await callback.answer()


@router.message(AdminMenuStates.menu, F.text == "👮‍♂️ Adminlar")
async def admin_roles_menu(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return
    await push_nav(state, "admin_roles")
    await show_admin_roles_menu(message, state)


@router.message(AdminMenuStates.menu, F.text == "💳 To‘lov kartalari")
async def admin_payment_cards_menu(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    await push_nav(state, "admin_payment_cards")
    await show_admin_payment_cards_menu(message, state)


@router.message(AdminPaymentCardsStates.menu, F.text == "➕ Karta qo‘shish")
async def admin_card_add_start(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return
    await state.set_state(AdminPaymentCardsStates.add_number)
    await message.answer("💳 Karta raqamini kiriting (mask yoki to‘liq):")


@router.message(AdminPaymentCardsStates.add_number)
async def admin_card_add_number(message: Message, state: FSMContext):
    number = (message.text or "").strip()
    if len(number) < 8:
        await message.answer("❌ Karta raqami noto‘g‘ri.")
        return
    await state.update_data(card_number=number)
    await state.set_state(AdminPaymentCardsStates.add_holder)
    await message.answer("👤 Karta egasi (ixtiyoriy). O‘tkazib yuborish uchun `-` yuboring.")


@router.message(AdminPaymentCardsStates.add_holder)
async def admin_card_add_holder(message: Message, state: FSMContext):
    holder = (message.text or "").strip()
    if holder == "-":
        holder = None
    await state.update_data(holder_name=holder)
    await state.set_state(AdminPaymentCardsStates.add_bank)
    await message.answer("🏦 Bank nomi (ixtiyoriy). O‘tkazib yuborish uchun `-` yuboring.")


@router.message(AdminPaymentCardsStates.add_bank)
async def admin_card_add_bank(message: Message, state: FSMContext):
    bank = (message.text or "").strip()
    if bank == "-":
        bank = None
    await state.update_data(bank_name=bank)
    await state.set_state(AdminPaymentCardsStates.add_sort)
    await message.answer("🔢 Tartib (sort_order). Masalan: 1. O‘tkazib yuborish uchun `-` yuboring.")


@router.message(AdminPaymentCardsStates.add_sort)
async def admin_card_add_sort(message: Message, state: FSMContext):
    sort_text = (message.text or "").strip()
    sort_order = 0
    if sort_text != "-":
        if not sort_text.isdigit():
            await message.answer("❌ Faqat raqam yoki `-` yuboring.")
            return
        sort_order = int(sort_text)
    await state.update_data(sort_order=sort_order)
    await state.set_state(AdminPaymentCardsStates.add_active)
    await message.answer("✅ Aktiv qilinsinmi? `ha` yoki `yo‘q` yuboring.")


@router.message(AdminPaymentCardsStates.add_active)
async def admin_card_add_active(message: Message, state: FSMContext):
    active_text = (message.text or "").strip().lower()
    active = active_text in {"ha", "yes", "1", "true"}
    data = await state.get_data()
    await db.execute(
        """
        INSERT INTO payment_cards (card_number, holder_name, bank_name, active, sort_order, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        data.get("card_number"),
        data.get("holder_name"),
        data.get("bank_name"),
        active,
        data.get("sort_order", 0),
        utc_now(),
        utc_now(),
    )
    await state.set_state(AdminPaymentCardsStates.menu)
    rows = await list_payment_cards(active_only=False)
    text = "💳 <b>TO‘LOV KARTALARI</b>\n\n"
    for row in rows:
        text += format_card_line(row) + "\n"
    await message.answer("✅ Karta qo‘shildi.\n\n" + text, reply_markup=admin_payment_cards_menu_keyboard())


@router.message(AdminPaymentCardsStates.menu, F.text == "✏️ Karta tahrirlash")
async def admin_card_edit_start(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return
    await state.set_state(AdminPaymentCardsStates.edit_select)
    await message.answer("✏️ Tahrirlash uchun karta ID yuboring:")


@router.message(AdminPaymentCardsStates.edit_select)
async def admin_card_edit_select(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ ID faqat raqam bo‘lishi kerak.")
        return
    card_id = int(message.text)
    row = await db.fetchrow("SELECT id FROM payment_cards WHERE id = $1", card_id)
    if not row:
        await message.answer("❌ Karta topilmadi.")
        return
    await state.update_data(card_id=card_id)
    await state.set_state(AdminPaymentCardsStates.edit_field)
    await message.answer(
        "Qaysi maydon?\n"
        "1 — Karta raqami\n"
        "2 — Karta egasi\n"
        "3 — Bank nomi\n"
        "4 — Tartib (sort_order)\n"
        "5 — Aktiv (ha/yo‘q)"
    )


@router.message(AdminPaymentCardsStates.edit_field)
async def admin_card_edit_field(message: Message, state: FSMContext):
    if message.text not in {"1", "2", "3", "4", "5"}:
        await message.answer("❌ 1-5 ni tanlang.")
        return
    field_map = {
        "1": "card_number",
        "2": "holder_name",
        "3": "bank_name",
        "4": "sort_order",
        "5": "active",
    }
    await state.update_data(field=field_map[message.text])
    await state.set_state(AdminPaymentCardsStates.edit_value)
    await message.answer("✍️ Yangi qiymatni yuboring:")


@router.message(AdminPaymentCardsStates.edit_value)
async def admin_card_edit_value(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("field")
    card_id = data.get("card_id")
    value = (message.text or "").strip()

    if field == "sort_order":
        if not value.isdigit():
            await message.answer("❌ Faqat raqam.")
            return
        value = int(value)
    if field == "active":
        value = value.lower() in {"ha", "yes", "1", "true"}

    await db.execute(
        f"""
        UPDATE payment_cards
        SET {field} = $1, updated_at = $2
        WHERE id = $3
        """,
        value,
        utc_now(),
        card_id,
    )
    await state.set_state(AdminPaymentCardsStates.menu)
    rows = await list_payment_cards(active_only=False)
    text = "💳 <b>TO‘LOV KARTALARI</b>\n\n"
    for row in rows:
        text += format_card_line(row) + "\n"
    await message.answer("✅ Karta yangilandi.\n\n" + text, reply_markup=admin_payment_cards_menu_keyboard())


@router.message(AdminPaymentCardsStates.menu, F.text == "❌ Karta o‘chirish")
async def admin_card_delete_start(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return
    await state.set_state(AdminPaymentCardsStates.delete_select)
    await message.answer("❌ O‘chirish uchun karta ID yuboring:")


@router.message(AdminPaymentCardsStates.delete_select)
async def admin_card_delete_select(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ ID faqat raqam bo‘lishi kerak.")
        return
    card_id = int(message.text)
    await db.execute("DELETE FROM payment_cards WHERE id = $1", card_id)
    await state.set_state(AdminPaymentCardsStates.menu)
    rows = await list_payment_cards(active_only=False)
    text = "💳 <b>TO‘LOV KARTALARI</b>\n\n"
    if not rows:
        text += "Hozircha karta yo‘q."
    else:
        for row in rows:
            text += format_card_line(row) + "\n"
    await message.answer("✅ Karta o‘chirildi.\n\n" + text, reply_markup=admin_payment_cards_menu_keyboard())


@router.message(AdminPaymentCardsStates.menu, F.text == "✅ Aktiv qilish")
async def admin_card_activate_start(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return
    await state.set_state(AdminPaymentCardsStates.activate_select)
    await message.answer("✅ Aktiv qilmoqchi bo‘lgan karta ID yuboring:")


@router.message(AdminPaymentCardsStates.activate_select)
async def admin_card_activate_select(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ ID faqat raqam bo‘lishi kerak.")
        return
    card_id = int(message.text)
    await db.execute(
        "UPDATE payment_cards SET active = TRUE, updated_at = $1 WHERE id = $2",
        utc_now(),
        card_id,
    )
    await state.set_state(AdminPaymentCardsStates.menu)
    rows = await list_payment_cards(active_only=False)
    text = "💳 <b>TO‘LOV KARTALARI</b>\n\n"
    for row in rows:
        text += format_card_line(row) + "\n"
    await message.answer("✅ Karta aktiv qilindi.\n\n" + text, reply_markup=admin_payment_cards_menu_keyboard())


@router.message(AdminPaymentCardsStates.menu, F.text == "🚫 Aktivni o‘chirish")
async def admin_card_deactivate_start(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return
    await state.set_state(AdminPaymentCardsStates.deactivate_select)
    await message.answer("🚫 Aktivini o‘chirmoqchi bo‘lgan karta ID yuboring:")


@router.message(AdminPaymentCardsStates.deactivate_select)
async def admin_card_deactivate_select(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ ID faqat raqam bo‘lishi kerak.")
        return
    card_id = int(message.text)
    await db.execute(
        "UPDATE payment_cards SET active = FALSE, updated_at = $1 WHERE id = $2",
        utc_now(),
        card_id,
    )
    await state.set_state(AdminPaymentCardsStates.menu)
    rows = await list_payment_cards(active_only=False)
    text = "💳 <b>TO‘LOV KARTALARI</b>\n\n"
    for row in rows:
        text += format_card_line(row) + "\n"
    await message.answer("✅ Karta deaktiv qilindi.\n\n" + text, reply_markup=admin_payment_cards_menu_keyboard())


@router.message(AdminPaymentCardsStates.menu, F.text == "⬅️ Orqaga")
async def admin_payment_cards_back(message: Message, state: FSMContext):
    await state.set_state(AdminMenuStates.menu)
    role = await get_admin_role(message.from_user.id)
    await message.answer("🛠 ADMIN PANEL", reply_markup=admin_menu_keyboard(role))


@router.message(AdminMenuStates.menu, F.text == "📌 Kanal ulash")
async def admin_logchat_menu(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return
    await state.set_state(AdminLogChatStates.menu)

    enabled = "✅ Yoqilgan" if await is_log_enabled() else "❌ O‘chirilgan"
    channel_username = await get_log_channel_username()
    chat_text = channel_username if channel_username else "—"

    text = (
        "📌 <b>KANAL LOG SOZLAMALARI</b>\n\n"
        f"🔗 Kanal username: {chat_text}\n"
        f"⚙️ Holat: {enabled}\n"
    )
    await message.answer(text, reply_markup=admin_logchat_menu_keyboard())


@router.message(AdminLogChatStates.menu, F.text == "🔗 Kanal username o‘rnatish")
async def admin_logchat_set_id_start(message: Message, state: FSMContext):
    await state.set_state(AdminLogChatStates.set_chat_id)
    await message.answer("Kanal username yuboring (masalan: @almaz_log):")


@router.message(AdminLogChatStates.set_chat_id)
async def admin_logchat_set_id_save(message: Message, state: FSMContext):
    raw = (message.text or "").strip()
    if not raw:
        await message.answer("❌ Username bo‘sh bo‘lishi mumkin emas.")
        return
    await set_setting("approved_channel_username", raw)
    await state.set_state(AdminLogChatStates.menu)
    await message.answer("✅ Username saqlandi.", reply_markup=admin_logchat_menu_keyboard())


@router.message(AdminLogChatStates.menu, F.text == "✅ Yoqish/O‘chirish")
async def admin_logchat_toggle(message: Message, state: FSMContext):
    current = await is_log_enabled()
    await set_setting("approved_channel_enabled", "false" if current else "true")
    await message.answer("✅ Holat yangilandi.", reply_markup=admin_logchat_menu_keyboard())


@router.message(AdminLogChatStates.menu, F.text == "🧪 Test yuborish")
async def admin_logchat_test(message: Message, state: FSMContext):
    try:
        channel_id, err = await resolve_log_channel_id(message.bot)
        if err:
            await message.answer(f"❌ {err}", reply_markup=admin_logchat_menu_keyboard())
            return
        await message.bot.send_message(channel_id, "✅ Log kanal test xabari.")
        await message.answer("✅ Test yuborildi.", reply_markup=admin_logchat_menu_keyboard())
    except TelegramBadRequest:
        await message.answer("❌ Kanal topilmadi. Username noto‘g‘ri yoki bot kanalga qo‘shilmagan.", reply_markup=admin_logchat_menu_keyboard())
    except TelegramForbiddenError:
        await message.answer("❌ Bot kanalga yozolmayapti. Botni kanalga admin qiling.", reply_markup=admin_logchat_menu_keyboard())
    except Exception:
        await message.answer("❌ Test yuborilmadi. Kanal sozlamasini tekshiring.", reply_markup=admin_logchat_menu_keyboard())


@router.message(AdminLogChatStates.menu, F.text == "⬅️ Orqaga")
async def admin_logchat_back(message: Message, state: FSMContext):
    await state.set_state(AdminMenuStates.menu)
    role = await get_admin_role(message.from_user.id)
    await message.answer("🛠 ADMIN PANEL", reply_markup=admin_menu_keyboard(role))


@router.message(F.text.in_({"⬅️ Orqaga", "🔙 Orqaga", "↩️ Orqaga"}))
async def admin_universal_back(message: Message, state: FSMContext):
    role = await get_admin_role(message.from_user.id)
    if not role:
        return
    stack = await get_nav_stack(state)
    if stack:
        stack.pop()
    key = stack[-1] if stack else None
    await state.set_state(None)
    await state.update_data(**{ADMIN_NAV_STACK_KEY: stack})
    await render_admin_menu_by_key(message, state, key)


@router.callback_query(F.data.in_({"back_admin", "admin_back"}))
async def admin_universal_back_callback(callback: CallbackQuery, state: FSMContext):
    role = await get_admin_role(callback.from_user.id)
    if not role:
        await callback.answer("⛔ Sizda ruxsat yo‘q", show_alert=True)
        return
    stack = await get_nav_stack(state)
    if stack:
        stack.pop()
    key = stack[-1] if stack else None
    await state.set_state(None)
    await state.update_data(**{ADMIN_NAV_STACK_KEY: stack})
    await render_admin_menu_by_key(callback.message, state, key)
    await callback.answer()

@router.message(AdminRoleStates.menu, F.text == "➕ Admin qo‘shish")
async def admin_role_add_start(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    await state.set_state(AdminRoleStates.add_id)
    await message.answer("➕ Admin qo‘shish uchun Telegram ID yuboring:")


@router.message(AdminRoleStates.add_id)
async def admin_role_add_id(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    if not message.text.isdigit():
        await message.answer("❌ ID faqat raqam bo‘lishi kerak")
        return

    await state.update_data(target_admin_id=int(message.text))
    await state.set_state(AdminRoleStates.add_role)
    await message.answer(
        "Rolni tanlang:\n"
        "1 — SUPERADMIN\n"
        "2 — MAIN ADMIN\n"
        "3 — VIEWER"
    )


@router.message(AdminRoleStates.add_role)
async def admin_role_add_save(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    new_role = parse_role(message.text)
    if not new_role:
        await message.answer("❌ Noto‘g‘ri rol. 1/2/3 yuboring.")
        return

    data = await state.get_data()
    target_id = data["target_admin_id"]

    await db.execute(
        """
        INSERT INTO admins (user_id, role, active, created_by, created_at)
        VALUES ($1, $2, TRUE, $3, $4)
        ON CONFLICT (user_id)
        DO UPDATE SET role = EXCLUDED.role, active = TRUE
        """,
        target_id,
        new_role,
        message.from_user.id,
        utc_now(),
    )

    await state.set_state(AdminRoleStates.menu)
    await message.answer(
        f"✅ Admin saqlandi: {target_id} — {ROLE_LABELS.get(new_role, new_role)}",
        reply_markup=admin_roles_menu_keyboard()
    )


@router.message(AdminRoleStates.menu, F.text == "✏️ Admin roli")
async def admin_role_edit_start(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    await state.set_state(AdminRoleStates.edit_select)
    await message.answer("✏️ Roli o‘zgartiriladigan admin ID ni yuboring:")


@router.message(AdminRoleStates.edit_select)
async def admin_role_edit_select(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    if not message.text.isdigit():
        await message.answer("❌ ID faqat raqam bo‘lishi kerak")
        return

    await state.update_data(target_admin_id=int(message.text))
    await state.set_state(AdminRoleStates.edit_role)
    await message.answer(
        "Yangi rol:\n"
        "1 — SUPERADMIN\n"
        "2 — MAIN ADMIN\n"
        "3 — VIEWER"
    )


@router.message(AdminRoleStates.edit_role)
async def admin_role_edit_save(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    new_role = parse_role(message.text)
    if not new_role:
        await message.answer("❌ Noto‘g‘ri rol. 1/2/3 yuboring.")
        return

    data = await state.get_data()
    target_id = data["target_admin_id"]

    await db.execute(
        "UPDATE admins SET role = $1, active = TRUE WHERE user_id = $2",
        new_role,
        target_id,
    )

    await state.set_state(AdminRoleStates.menu)
    await message.answer(
        f"✅ Rol yangilandi: {target_id} — {ROLE_LABELS.get(new_role, new_role)}",
        reply_markup=admin_roles_menu_keyboard()
    )


@router.message(AdminRoleStates.menu, F.text == "❌ Admin o‘chirish")
async def admin_role_remove_start(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    await state.set_state(AdminRoleStates.remove_select)
    await message.answer("❌ O‘chiriladigan admin ID ni yuboring:")


@router.message(AdminRoleStates.remove_select)
async def admin_role_remove_save(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    if not message.text.isdigit():
        await message.answer("❌ ID faqat raqam bo‘lishi kerak")
        return

    target_id = int(message.text)

    await db.execute(
        "UPDATE admins SET active = FALSE WHERE user_id = $1",
        target_id,
    )

    await state.set_state(AdminRoleStates.menu)
    await message.answer(
        f"✅ Admin o‘chirildi: {target_id}",
        reply_markup=admin_roles_menu_keyboard()
    )


@router.message(AdminRoleStates.menu, F.text == "⬅️ Orqaga")
async def admin_role_back(message: Message, state: FSMContext):
    await state.set_state(AdminMenuStates.menu)
    role = await get_admin_role(message.from_user.id)
    await message.answer(
        "🛠 ADMIN PANEL",
        reply_markup=admin_menu_keyboard(role)
    )


@router.message(AdminRoleStates.add_id, F.text == "⬅️ Orqaga")
@router.message(AdminRoleStates.add_role, F.text == "⬅️ Orqaga")
@router.message(AdminRoleStates.edit_select, F.text == "⬅️ Orqaga")
@router.message(AdminRoleStates.edit_role, F.text == "⬅️ Orqaga")
@router.message(AdminRoleStates.remove_select, F.text == "⬅️ Orqaga")
async def admin_role_back_to_list(message: Message, state: FSMContext):
    await state.set_state(AdminRoleStates.menu)
    rows = await db.fetch(
        "SELECT user_id, role, active FROM admins ORDER BY role, user_id"
    )
    text = "👮‍♂️ <b>ADMINLAR</b>\n\n"
    if not rows:
        text += "Hozircha adminlar yo‘q."
    else:
        for row in rows:
            r = row["role"]
            status = "🟢" if row["active"] else "🔴"
            text += f"{status} {row['user_id']} — {ROLE_LABELS.get(r, r)}\n"

    await message.answer(text, reply_markup=admin_roles_menu_keyboard())

@router.callback_query(F.data == "prices")
async def prices_handler(callback: CallbackQuery):
    row = await db.fetchrow(
        "SELECT value FROM settings WHERE key = $1",
        "prices_text",
    )
    prices_text = row["value"] if row else ""

    await safe_edit(callback, prices_text, reply_markup=prices_back_inline())
    await callback.answer()

@router.callback_query(F.data == "prices_back")
async def prices_back_handler(callback: CallbackQuery):
    await show_main_menu_callback(callback)
    await callback.answer()

@router.message(AdminMenuStates.menu, F.text == "💰 Narxlar matnini tahrirlash")
async def admin_edit_prices(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    await state.set_state(AdminEditPricesStates.waiting_text)

    await message.answer(
        "✍️ Yangi narxlar matnini yuboring:\n\n"
        "Markdown ishlatish mumkin.\n"
        "Masalan:\n"
        "200 💎 — 25 000 so‘m",
        reply_markup=back_only_keyboard()
    )

@router.message(AdminEditPricesStates.waiting_text)
async def admin_save_prices(message: Message, state: FSMContext):
    if message.text == "⬅️ Orqaga":
        await state.set_state(AdminMenuStates.menu)
        role = await get_admin_role(message.from_user.id)
        await message.answer(
            "🛠 ADMIN PANEL\n\nKerakli bo‘limni tanlang:",
            reply_markup=admin_menu_keyboard(role)
        )
        return
    await db.execute(
        "UPDATE settings SET value = $1 WHERE key = $2",
        message.text,
        "prices_text",
    )

    await state.set_state(AdminMenuStates.menu)

    role = await get_admin_role(message.from_user.id)
    await message.answer(
        "✅ Narxlar muvaffaqiyatli yangilandi",
        reply_markup=admin_menu_keyboard(role)
    )

@router.message(AdminMenuStates.menu, F.text == "🧾 Buyurtmalar")
async def admin_orders_menu(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER, ADMIN_ROLE_MAIN, ADMIN_ROLE_VIEWER))
    if not role:
        return
    await push_nav(state, "admin_orders")

    orders = await db.fetch(
        """
        SELECT id, product_name, almaz, price, status
        FROM orders
        ORDER BY id DESC
        LIMIT 10
        """
    )

    if not orders:
        await message.answer("🧾 Buyurtmalar yo‘q")
        return

    text = "🧾 OXIRGI 10 BUYURTMA\n\n"

    for o in orders:
        text += (
            f"🆔 #{o['id']} | {o['status']}\n"
            f"📦 {o['product_name']} | 💎 {o['almaz']} | 💰 {o['price']:,} so‘m\n\n"
        )

    text += (
        "✍️ Batafsil ko‘rish uchun BUYURTMA ID ni yuboring\n"
        "⬅️ Orqaga qaytish uchun tugmani bosing"
    )

    await state.set_state(AdminOrdersStates.waiting_order_id)
    await message.answer(text, reply_markup=orders_back_keyboard())

@router.message(AdminMenuStates.menu, F.text == "📊 Daromad statistikasi")
async def admin_revenue_stats(message: Message):
    role = await require_role(message, PERM_REVENUE_ROLES)
    if not role:
        return

    now = utc_now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    periods = {
        "Bugun": today_start,
        "Oxirgi 7 kun": now - timedelta(days=7),
        "Oxirgi 30 kun": now - timedelta(days=30),
    }

    text = "📊 DAROMAD STATISTIKASI\n\n"

    # 🟢 BUYURTMALAR SONI + DAROMAD
    for title, since in periods.items():
        row = await db.fetchrow(
            """
            SELECT 
                COUNT(*) AS cnt,
                COALESCE(SUM(price), 0) AS total
            FROM orders
            WHERE status = 'approved' AND created_at >= $1
            """,
            since,
        )
        count, total = row["cnt"], row["total"]

        text += (
            f"🗓 {title}\n"
            f"🧾 Buyurtmalar: {count}\n"
            f"💰 Daromad: {total:,} so‘m\n\n"
        )   

    # 🔥 OXIRGI 7 KUNLIK TOP PAKETLAR
    week_ago = now - timedelta(days=7)

    top_packages = await db.fetch(
        """
        SELECT product_name, SUM(quantity) AS qty_sum, SUM(price) AS price_sum
        FROM orders
        WHERE status = 'approved' AND created_at >= $1
        GROUP BY product_name
        ORDER BY SUM(price) DESC
        LIMIT 3
        """,
        week_ago,
    )

    if top_packages:
        text += "🔥 OXIRGI 7 KUNLIK TOP PAKETLAR\n\n"
        for row in top_packages:
            name = row["product_name"]
            qty = row["qty_sum"]
            total_sum = row["price_sum"]
            text += (
                f"📦 {name}\n"
                f"🧾 {qty} ta | 💰 {total_sum:,} so‘m\n\n"
            )

    # ✅ FAQAT BIR MARTA XABAR YUBORILADI
    await message.answer(text)


async def build_admin_stats_list():
    rows = await db.fetch(
        """
        SELECT a.user_id, a.role, a.active, u.username, u.first_name
        FROM admins a
        LEFT JOIN users u ON u.user_id = a.user_id
        ORDER BY a.role, a.user_id
        """
    )
    admins = []
    for row in rows:
        status = "ON" if row["active"] else "OFF"
        if row["username"]:
            name = f"@{row['username']}"
        elif row["first_name"]:
            name = row["first_name"]
        else:
            name = str(row["user_id"])
        role_label = ROLE_LABELS.get(row["role"], row["role"])
        label = f"{status} {name} ({role_label})"
        admins.append({"user_id": row["user_id"], "label": label})
    return admins


@router.message(AdminMenuStates.menu, F.text == "Admins statics")
async def admin_stats_menu(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER, ADMIN_ROLE_MAIN))
    if not role:
        return
    await state.set_state(AdminStatsStates.menu)
    admins = await build_admin_stats_list()
    text = "Adminlar ro'yxati\n\nAdminni tanlang:"
    if not admins:
        text = "Adminlar ro'yxati\n\nHozircha adminlar yo'q."
    await message.answer(
        text,
        reply_markup=admin_stats_admins_keyboard(admins) if admins else None,
    )


@router.callback_query(F.data == "admin_stats_back")
async def admin_stats_back(callback: CallbackQuery, state: FSMContext):
    role = await get_admin_role(callback.from_user.id)
    if role not in (ADMIN_ROLE_SUPER, ADMIN_ROLE_MAIN):
        await callback.answer("Sizda ruxsat yo'q", show_alert=True)
        return
    await state.set_state(AdminStatsStates.menu)
    admins = await build_admin_stats_list()
    text = "Adminlar ro'yxati\n\nAdminni tanlang:"
    if not admins:
        text = "Adminlar ro'yxati\n\nHozircha adminlar yo'q."
    await safe_edit(
        callback,
        text,
        reply_markup=admin_stats_admins_keyboard(admins) if admins else None,
        allow_photo=True,
    )
    await callback.answer()


@router.callback_query(F.data == "admin_stats_back_menu")
async def admin_stats_back_menu(callback: CallbackQuery, state: FSMContext):
    role = await get_admin_role(callback.from_user.id)
    if role not in (ADMIN_ROLE_SUPER, ADMIN_ROLE_MAIN):
        await callback.answer("Sizda ruxsat yo'q", show_alert=True)
        return
    await state.set_state(AdminMenuStates.menu)
    try:
        await callback.message.delete()
    except Exception:
        await safe_edit(callback, "ADMIN PANEL", reply_markup=None, allow_photo=True)
    await callback.message.answer("ADMIN PANEL", reply_markup=admin_menu_keyboard(role))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_stats_select:"))
async def admin_stats_select(callback: CallbackQuery, state: FSMContext):
    role = await get_admin_role(callback.from_user.id)
    if role not in (ADMIN_ROLE_SUPER, ADMIN_ROLE_MAIN):
        await callback.answer("Sizda ruxsat yo'q", show_alert=True)
        return
    try:
        _, admin_id = callback.data.split(":")
        admin_id = int(admin_id)
    except Exception:
        await callback.answer("Ma'lumot xato", show_alert=True)
        return

    admin_row = await db.fetchrow(
        """
        SELECT a.user_id, a.role, u.username, u.first_name
        FROM admins a
        LEFT JOIN users u ON u.user_id = a.user_id
        WHERE a.user_id = $1
        """
        ,
        admin_id,
    )
    if not admin_row:
        await callback.answer("Admin topilmadi", show_alert=True)
        return

    if admin_row["username"]:
        admin_name = f"@{admin_row['username']}"
    elif admin_row["first_name"]:
        admin_name = admin_row["first_name"]
    else:
        admin_name = str(admin_row["user_id"])

    counts = await db.fetchrow(
        """
        SELECT
            COALESCE(SUM(CASE WHEN action = 'ORDER_APPROVED' THEN 1 ELSE 0 END), 0) AS approved_count,
            COALESCE(SUM(CASE WHEN action = 'ORDER_REJECTED' THEN 1 ELSE 0 END), 0) AS rejected_count,
            COALESCE(SUM(CASE WHEN action = 'ORDER_EDITED' THEN 1 ELSE 0 END), 0) AS edited_count
        FROM admin_logs
        WHERE admin_id = $1
        """
        ,
        admin_id,
    )

    revenue = await db.fetchrow(
        """
        SELECT
            COALESCE(SUM(price), 0) AS total_revenue,
            COALESCE(SUM(almaz), 0) AS total_almaz
        FROM orders
        WHERE status = 'approved' AND admin_id = $1
        """
        ,
        admin_id,
    )

    text = (
        f"Admin: {admin_name} ({admin_id})\n\n"
        f"✅ Tasdiqlagan: {counts['approved_count']} ta\n"
        f"❌ Bekor qilgan: {counts['rejected_count']} ta\n"
        f"✏️ Tahrirlagan: {counts['edited_count']} ta\n\n"
        f"💰 Aylantirgan summa: {format_money(revenue['total_revenue'])} so'm\n"
        f"💎 Tasdiqlangan jami almaz: {format_money(revenue['total_almaz'])}"
    )

    await state.set_state(AdminStatsStates.detail)
    await safe_edit(
        callback,
        text,
        reply_markup=admin_stats_detail_keyboard(),
        allow_photo=True,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy_pkg:"))
async def package_selected_handler(callback: CallbackQuery, state: FSMContext):
    pkg_id = int(callback.data.split(":")[1])

    pkg = await db.fetchrow(
        "SELECT name, almaz, price FROM packages WHERE id = $1 AND active = TRUE",
        pkg_id,
    )

    if not pkg:
        await callback.answer("❌ Paket topilmadi", show_alert=True)
        return

    name, almaz, price = pkg["name"], pkg["almaz"], pkg["price"]

    # 🔥 VOUCHER bo‘lsa
    if "haftalik" in name.lower() or "oylik" in name.lower():
        await state.update_data(
            package_id=pkg_id,
            name=name,
            almaz=almaz,
            price=price,
            is_voucher=True
        )

        await state.set_state(VoucherStates.choosing_quantity)

        await safe_edit(
            callback,
            f"{name}\n\n"
            f"💎 {almaz} almaz / 1 dona\n"
            f"💰 {price:,} so‘m / 1 dona\n\n"
            "🧮 Nechta dona olmoqchisiz?",
            reply_markup=voucher_quantity_keyboard(pkg_id)
        )
        await callback.answer()
        return

    # ✅ ODDIY ALMAZ PAKET (ESKI ISHLAYOTGAN LOGIKA)
    await state.update_data(
        package_id=pkg_id,
        package_name=name,
        almaz=almaz,
        price=price
    )

    await state.set_state(OrderStates.confirming_package)

    await safe_edit(
        callback,
        "✅ <b>PAKET TANLANDI</b>\n\n"
        f"📦 Paket: {name}\n"
        f"💎 Almaz: {almaz}\n"
        f"💰 Narx: {price:,} so‘m\n\n"
        "⚡ Yetkazish: 5–15 daqiqa\n"
        "🔒 Xavfsiz va kafolatlangan\n\n"
        "👉 Davom etamizmi?",
        reply_markup=confirm_package_keyboard()
    )

    await callback.answer()

@router.message(AdminMenuStates.menu, F.text == "🎁 Promokodlar")
async def admin_promocode_menu(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return
    await push_nav(state, "admin_promocodes")
    await show_admin_promocode_menu(message, state)

@router.message(AdminPromoStates.menu, F.text == "➕ Promokod yaratish")
async def admin_add_promo_start(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    await state.set_state(AdminPromoStates.add_code)
    await message.answer(
        "🔤 Promokod nomini kiriting:",
        reply_markup=promo_input_cancel_keyboard()
    )



@router.message(AdminPromoStates.add_code)
async def admin_add_promo_code(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return
    if message.text == "❌ Bekor qilish":
        await state.set_state(AdminPromoStates.menu)
        await message.answer(
            "Bekor qilindi.",
            reply_markup=admin_promocode_menu_keyboard()
        )
        return
    if not message.text or message.text.strip().startswith("➕"):
        await message.answer("❌ Promokod nomini oddiy matn qilib kiriting.")
        return

    await state.update_data(code=message.text.upper())
    await state.set_state(AdminPromoStates.add_almaz)

    await message.answer("💎 Nechta almaz beriladi?", reply_markup=promo_input_cancel_keyboard())

@router.message(AdminPromoStates.add_almaz)
async def admin_add_promo_almaz(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return
    if message.text == "❌ Bekor qilish":
        await state.set_state(AdminPromoStates.menu)
        await message.answer(
            "Bekor qilindi.",
            reply_markup=admin_promocode_menu_keyboard()
        )
        return

    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting")
        return

    await state.update_data(almaz=int(message.text))
    await state.set_state(AdminPromoStates.add_max_uses)

    await message.answer("👥 Nechta odam ishlata oladi?", reply_markup=promo_input_cancel_keyboard())

@router.message(AdminPromoStates.add_max_uses)
async def admin_add_promo_limit(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return
    if message.text == "❌ Bekor qilish":
        await state.set_state(AdminPromoStates.menu)
        await message.answer(
            "Bekor qilindi.",
            reply_markup=admin_promocode_menu_keyboard()
        )
        return

    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting")
        return

    await state.update_data(max_uses=int(message.text))
    await state.set_state(AdminPromoStates.add_expire)

    await message.answer(
        "⏰ Amal qilish muddati (kunlarda).\n"
        "Agar cheklanmasin desangiz: 0 yozing",
        reply_markup=promo_input_cancel_keyboard()
    )

@router.message(AdminPromoStates.add_expire)
async def admin_add_promo_save(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return
    if message.text == "❌ Bekor qilish":
        await state.set_state(AdminPromoStates.menu)
        await message.answer(
            "Bekor qilindi.",
            reply_markup=admin_promocode_menu_keyboard()
        )
        return

    data = await state.get_data()
    now = utc_now()

    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting")
        return

    days = int(message.text)
    expires_at = None

    if days > 0:
        expires_at = now + timedelta(days=days)

    await db.execute(
        """
        INSERT INTO promocodes (
            code, almaz_reward, max_uses, expires_at, created_at
        )
        VALUES ($1, $2, $3, $4, $5)
        """,
        data["code"],
        data["almaz"],
        data["max_uses"],
        expires_at,
        now,
    )
    await state.set_state(AdminPromoStates.menu)

    await message.answer(
        "✅ Promokod muvaffaqiyatli yaratildi!",
        reply_markup=admin_promocode_menu_keyboard()
    )


@router.callback_query(AdminPromoStates.add_code)
@router.callback_query(AdminPromoStates.add_almaz)
@router.callback_query(AdminPromoStates.add_max_uses)
@router.callback_query(AdminPromoStates.add_expire)
async def admin_promo_input_callback_guard(callback: CallbackQuery):
    await callback.answer("Iltimos promokod ma’lumotini matn qilib kiriting.", show_alert=True)


@router.message(AdminMenuStates.menu, F.text == "📦 Paketlar")
async def admin_packages_menu(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    await push_nav(state, "admin_packages")
    await show_admin_packages_menu(message, state)

@router.message(AdminPackagesStates.menu, F.text == "➕ Paket qo‘shish")
async def admin_add_package_start(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    await state.set_state(AdminPackagesStates.add_name)
    await message.answer("✍️ Paket nomini kiriting:\nMasalan: 1000 💎")

@router.message(AdminPackagesStates.add_name)
async def admin_add_package_name(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    await state.update_data(name=message.text)
    await state.set_state(AdminPackagesStates.add_almaz)

    await message.answer("💎 Almaz miqdorini kiriting:\nMasalan: 1000")

@router.message(AdminPackagesStates.add_almaz)
async def admin_add_package_almaz(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting")
        return

    await state.update_data(almaz=int(message.text))
    await state.set_state(AdminPackagesStates.add_price)

    await message.answer("💰 Narxni kiriting (so‘m):\nMasalan: 120000")

@router.message(AdminPackagesStates.add_price)
async def admin_add_package_price(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting")
        return

    data = await state.get_data()

    await db.execute(
        "INSERT INTO packages (name, almaz, price) VALUES ($1, $2, $3)",
        data["name"],
        data["almaz"],
        int(message.text),
    )

    await state.set_state(AdminPackagesStates.menu)

    await message.answer(
        "✅ Paket muvaffaqiyatli qo‘shildi",
        reply_markup=admin_packages_menu_keyboard()
    )

@router.message(AdminPackagesStates.menu, F.text == "✏️ Paket tahrirlash")
async def admin_edit_package_start(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    packages = await db.fetch(
        "SELECT id, name FROM packages WHERE active = TRUE"
    )

    if not packages:
        await message.answer("❌ Tahrirlash uchun paket yo‘q")
        return

    text = "✏️ Tahrirlash uchun paketni TANLANG:\n\n"
    for pkg in packages:
        text += f"{pkg['id']}. {pkg['name']}\n"

    await state.set_state(AdminPackagesStates.edit_select)
    await message.answer(text)

@router.message(AdminPackagesStates.edit_select)
async def admin_edit_package_choose(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    if not message.text.isdigit():
        await message.answer("❌ Paket raqamini kiriting")
        return

    pkg_id = int(message.text)

    row = await db.fetchrow(
        "SELECT id FROM packages WHERE id = $1 AND active = TRUE",
        pkg_id,
    )
    if not row:
        await message.answer("❌ Paket topilmadi")
        return

    await state.update_data(package_id=pkg_id)
    await state.set_state(AdminPackagesStates.edit_field)

    await message.answer(
        "Qaysi maydonni o‘zgartiramiz?\n\n"
        "1 — Nomi\n"
        "2 — Almaz miqdori\n"
        "3 — Narxi"
    )

@router.message(AdminPackagesStates.edit_field)
async def admin_edit_package_field(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    if message.text not in ["1", "2", "3"]:
        await message.answer("❌ 1, 2 yoki 3 ni tanlang")
        return

    field_map = {
        "1": "name",
        "2": "almaz",
        "3": "price"
    }

    await state.update_data(field=field_map[message.text])
    await state.set_state(AdminPackagesStates.edit_value)

    await message.answer("✍️ Yangi qiymatni kiriting")

@router.message(AdminPackagesStates.edit_value)
async def admin_edit_package_save(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    data = await state.get_data()
    field = data["field"]
    pkg_id = data["package_id"]

    value = message.text

    if field in ["almaz", "price"] and not value.isdigit():
        await message.answer("❌ Faqat raqam kiriting")
        return

    await db.execute(
        f"UPDATE packages SET {field} = $1 WHERE id = $2",
        value,
        pkg_id,
    )

    await state.set_state(AdminPackagesStates.menu)

    await message.answer(
        "✅ Paket muvaffaqiyatli yangilandi",
        reply_markup=admin_packages_menu_keyboard()
    )

@router.message(AdminPackagesStates.menu, F.text == "❌ Paket o‘chirish")
async def admin_delete_package_start(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    packages = await db.fetch(
        "SELECT id, name FROM packages"
    )

    if not packages:
        await message.answer("❌ O‘chirish uchun paket yo‘q")
        return

    text = "❌ O‘chirmoqchi bo‘lgan paket RAQAMINI yuboring:\n\n"
    for pkg in packages:
        text += f"{pkg['id']}. {pkg['name']}\n"

    await state.set_state(AdminPackagesStates.delete_select)
    await message.answer(text)

@router.message(AdminPackagesStates.delete_select)
async def admin_delete_package_confirm(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    if not message.text.isdigit():
        await message.answer("❌ Faqat paket raqamini yuboring")
        return

    pkg_id = int(message.text)

    row = await db.fetchrow(
        "SELECT id FROM packages WHERE id = $1",
        pkg_id,
    )
    if not row:
        await message.answer("❌ Bunday paket yo‘q")
        return

    await db.execute(
        "DELETE FROM packages WHERE id = $1",
        pkg_id,
    )

    await state.set_state(AdminPackagesStates.menu)

    await message.answer(
        "✅ Paket to‘liq o‘chirildi",
        reply_markup=admin_packages_menu_keyboard()
    )

@router.message(AdminPackagesStates.menu, F.text == "⬅️ Orqaga")
async def admin_packages_back(message: Message, state: FSMContext):
    # paketlar state’dan chiqamiz
    await state.set_state(AdminMenuStates.menu)

    role = await get_admin_role(message.from_user.id)
    await message.answer(
        "🛠 ADMIN PANEL",
        reply_markup=admin_menu_keyboard(role)
    )

async def build_balance_text(user_id: int, first_name: str) -> str | None:
    row = await db.fetchrow(
        """
        SELECT almaz_balance, bonus_almaz, total_almaz
        FROM users WHERE user_id = $1
        """,
        user_id,
    )
    if not row:
        return None
    almaz_balance, bonus_almaz, total_almaz = (
        row["almaz_balance"],
        row["bonus_almaz"],
        row["total_almaz"],
    )
    return (
        "BALANS MA'LUMOTI\n\n"
        f"Ism: {first_name}\n"
        f"Umumiy balansingiz: {almaz_balance} almaz\n"
        f"Bonus orqali olingan: {bonus_almaz} almaz\n\n"
        f"Jami sotib olingan: {total_almaz} almaz\n\n"
        "Sotib olingan almazlar balansga yozilmaydi, to'g'ridan-to'g'ri FF akkauntga beriladi.\n"
        "Har bir xariddan % bonus qaytariladi"
    )


@router.message(Command("balance"))
async def balance_command(message: Message):
    text = await build_balance_text(message.from_user.id, message.from_user.first_name)
    if not text:
        await message.answer("Foydalanuvchi topilmadi")
        return
    await message.answer(text, reply_markup=promo_enter_keyboard())


@router.callback_query(F.data == "balance")
async def balance_handler(callback: CallbackQuery):
    text = await build_balance_text(callback.from_user.id, callback.from_user.first_name)
    if not text:
        await callback.answer("Foydalanuvchi topilmadi", show_alert=True)
        return
    await safe_edit(callback, text, reply_markup=promo_enter_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("wd_amount:"))
async def withdraw_choose_amount(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = await get_user(user_id)
    if not user:
        await callback.answer("Foydalanuvchi topilmadi.", show_alert=True)
        return

    balance = user["almaz_balance"] or 0
    try:
        amount = int(callback.data.split(":")[1])
    except ValueError:
        await callback.answer("Noto'g'ri miqdor.", show_alert=True)
        return

    if balance < amount:
        await callback.answer("Balansingiz o'zgargan, yechish uchun yetarli emas.", show_alert=True)
        return

    await state.set_state(WithdrawStates.waiting_ff_id)
    await state.update_data(withdraw_amount=amount)

    await callback.message.answer(
        "🎮 Endi, almaz yechmoqchi bo'lgan Free Fire akkauntingiz <b>ID raqamini</b> yuboring.\n\n"
        "ID ni diqqat bilan tekshirib yuboring — almaz aynan shu akkauntga tushiriladi.",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(WithdrawStates.waiting_ff_id)
async def withdraw_receive_ff_id(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    amount = data.get("withdraw_amount")
    ff_id = (message.text or "").strip()

    if not amount or not ff_id:
        await message.answer("❌ Noto'g'ri ma'lumot. /start yuborib qayta urinib ko'ring.")
        await state.clear()
        return

    if len(ff_id) < 3:
        await message.answer("⚠️ Free Fire ID juda qisqa ko'rinmoqda. Iltimos, qayta tekshirib yuboring.")
        return

    request_id = await create_withdraw_request(user_id, int(amount), ff_id)
    await state.clear()

    await message.answer(
        "✅ Almaz yechish bo'yicha so'rovingiz qabul qilindi!\n\n"
        f"📥 Miqdor: <b>{amount} Almaz</b>\n"
        f"🎮 Free Fire ID: <code>{ff_id}</code>\n\n"
        "Almaz 24 soat ichida Free Fire akkauntingizga tushiriladi. Iltimos, sabr qiling 🙂",
        parse_mode="HTML"
    )

    await notify_admins_about_withdraw(message.bot, request_id)


# ============== Withdraw admin callbacklari ==============
@router.callback_query(F.data.startswith("wd_ok:"))
async def withdraw_approve(callback: CallbackQuery):
    if not await is_owner_or_admin(callback.from_user.id):
        await callback.answer("Sizda bu amal uchun ruxsat yo'q.", show_alert=True)
        return
    try:
        req_id = int(callback.data.split(":")[1])
    except ValueError:
        await callback.answer("Noto'g'ri so'rov.", show_alert=True)
        return

    req = await get_withdraw_request(req_id)
    if not req:
        await callback.answer("So'rov topilmadi yoki o'chirib yuborilgan.", show_alert=True)
        return

    if req["status"] != "pending":
        await callback.answer(f"Bu so'rov allaqachon '{req['status']}' holatida.", show_alert=True)
        return

    user_id = req["user_id"]
    amount = req["amount"]
    ff_id = req["ff_id"]

    user = await get_user(user_id)
    balance = user["almaz_balance"] if user else 0
    if balance < amount:
        await callback.answer("Foydalanuvchi balansida bu miqdor yetarli emas.", show_alert=True)
        return

    await add_almaz(user_id, -amount)
    await update_withdraw_status(req_id, "approved", callback.from_user.id, None)
    await update_withdraw_admin_messages(callback.bot, req_id, "✅ Tasdiqlandi")
    await log_admin_action(
        admin_id=callback.from_user.id,
        action="WITHDRAW_APPROVED",
        order_id=None,
        details=f"withdraw_request:{req_id}",
    )

    try:
        await callback.bot.send_message(
            user_id,
            "🎉 Almaz yechish so'rovingiz tasdiqlandi!\n\n"
            f"💎 Miqdor: <b>{amount} Almaz</b>\n"
            "Almazingiz Free Fire akkauntingizga muvaffaqiyatli tashlab berildi. Rahmat! 😊",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await send_proof_receipt(callback.bot, req_id, user_id, amount, ff_id)
    log_err = await send_withdraw_log_if_needed(callback.bot, req_id, callback.from_user)
    if log_err:
        await callback.message.answer(f"⚠️ {log_err}")
    await callback.answer("So'rov tasdiqlandi.")


@router.callback_query(F.data.startswith("wd_reject:"))
async def withdraw_reject(callback: CallbackQuery):
    if not await is_owner_or_admin(callback.from_user.id):
        await callback.answer("Sizda bu amal uchun ruxsat yo'q.", show_alert=True)
        return
    try:
        req_id = int(callback.data.split(":")[1])
    except ValueError:
        await callback.answer("Noto'g'ri so'rov.", show_alert=True)
        return

    req = await get_withdraw_request(req_id)
    if not req:
        await callback.answer("So'rov topilmadi yoki o'chirib yuborilgan.", show_alert=True)
        return

    if req["status"] != "pending":
        await callback.answer(f"Bu so'rov allaqachon '{req['status']}' holatida.", show_alert=True)
        return

    await update_withdraw_status(req_id, "rejected", callback.from_user.id, None)
    await update_withdraw_admin_messages(callback.bot, req_id, "❌ Rad etildi")
    await log_admin_action(
        admin_id=callback.from_user.id,
        action="WITHDRAW_REJECTED",
        order_id=None,
        details=f"withdraw_request:{req_id}",
    )

    try:
        await callback.bot.send_message(
            req["user_id"],
            "❌ Almaz yechish bo'yicha so'rovingiz rad etildi.\n\n"
            "Bunga turli sabablar bo'lishi mumkin (qoidabuzarlik, noto'g'ri ma'lumot va hokazo).\n"
            "Agar bu xatolik deb o'ylasangiz, qo'llab-quvvatlashga murojaat qilishingiz mumkin.",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await callback.answer("So'rov rad etildi.")


@router.callback_query(F.data.startswith("wd_edit:"))
async def withdraw_edit_start(callback: CallbackQuery, state: FSMContext):
    if not await is_owner_or_admin(callback.from_user.id):
        await callback.answer("Sizda bu amal uchun ruxsat yo'q.", show_alert=True)
        return
    try:
        req_id = int(callback.data.split(":")[1])
    except ValueError:
        await callback.answer("Noto'g'ri so'rov.", show_alert=True)
        return

    req = await get_withdraw_request(req_id)
    if not req:
        await callback.answer("So'rov topilmadi yoki o'chirib yuborilgan.", show_alert=True)
        return
    if req["status"] != "pending":
        await callback.answer(f"Bu so'rov allaqachon '{req['status']}' holatida.", show_alert=True)
        return

    await state.set_state(WithdrawEdit.waiting_text)
    await state.update_data(edit_request_id=req_id)

    await callback.message.answer(
        "✏️ Foydalanuvchiga yuboriladigan xabar matnini kiriting.\n"
        "Masalan: Free Fire ID noto'g'ri ko'rsatilgan, iltimos, qayta yuboring."
    )
    await callback.answer()


@router.message(WithdrawEdit.waiting_text)
async def withdraw_edit_send(message: Message, state: FSMContext):
    if not await is_owner_or_admin(message.from_user.id):
        return
    data = await state.get_data()
    req_id = data.get("edit_request_id")
    if not req_id:
        await state.clear()
        await message.answer("❌ So'rov topilmadi. Qaytadan urinib ko'ring.")
        return

    note = (message.text or "").strip()
    req = await get_withdraw_request(int(req_id))
    if not req:
        await state.clear()
        await message.answer("❌ So'rov bazadan topilmadi.")
        return

    if req["status"] != "pending":
        await state.clear()
        await message.answer(f"ℹ️ Bu so'rov allaqachon '{req['status']}' holatiga o'tkazilgan.")
        return

    try:
        await message.bot.send_message(
            req["user_id"],
            f"✏️ Almaz yechish so'rovi bo'yicha xabar:\n\n{note}"
        )
    except Exception:
        pass

    await update_withdraw_status(int(req_id), "edited", message.from_user.id, note)
    await update_withdraw_admin_messages(message.bot, int(req_id), "✏️ Tahrirlandi")
    await log_admin_action(
        admin_id=message.from_user.id,
        action="WITHDRAW_EDITED",
        order_id=None,
        details=f"withdraw_request:{req_id}",
    )

    await state.clear()
    role = await get_admin_role(message.from_user.id)
    await message.answer(
        "✅ Izoh foydalanuvchiga yuborildi va so'rov <b>tahrirlandi</b> holatiga o'tkazildi.",
        parse_mode="HTML",
        reply_markup=admin_menu_keyboard(role) if role else None
    )

@router.callback_query(F.data == "contact_admin")
async def contact_admin_handler(callback: CallbackQuery):
    row = await db.fetchrow(
        "SELECT value FROM settings WHERE key = $1",
        "admin_contact_text",
    )
    text = row["value"] if row else "📞 Admin bilan bog‘lanish uchun admin yozing."

    await safe_edit(callback, text, reply_markup=prices_back_inline())
    await callback.answer()

@router.message(AdminMenuStates.menu, F.text == "📞 Admin bilan bog‘lanish matni")
async def admin_edit_contact_text(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    await state.set_state(AdminContactTextStates.waiting_text)

    await message.answer(
        "✍️ Foydalanuvchilarga chiqadigan ADMIN bilan bog‘lanish matnini yuboring:\n\n"
        "Markdown ishlatish mumkin.",
        reply_markup=back_only_keyboard()
    )

@router.message(AdminMenuStates.menu, F.text == "Asosiy menyu textini o'zgartirish")
async def admin_edit_main_menu_text(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER, ADMIN_ROLE_MAIN))
    if not role:
        return
    await state.set_state(MainMenuTextEditState.waiting_text)
    await message.answer(
        "Yangi asosiy menyu matnini yuboring. Bekor qilish uchun Orqaga",
        reply_markup=main_menu_text_back_keyboard()
    )


@router.message(MainMenuTextEditState.waiting_text)
async def admin_save_main_menu_text(message: Message, state: FSMContext):
    if not message.text:
        return
    if message.text.strip() == "Orqaga":
        await state.set_state(AdminMenuStates.menu)
        role = await get_admin_role(message.from_user.id)
        await message.answer(
            "ADMIN PANEL\n\nKerakli bo'limni tanlang:",
            reply_markup=admin_menu_keyboard(role)
        )
        return
    if message.text.strip().startswith("/"):
        return
    await set_setting("main_menu_text", message.text)
    await state.set_state(AdminMenuStates.menu)
    role = await get_admin_role(message.from_user.id)
    await message.answer(
        "Saqlandi",
        reply_markup=admin_menu_keyboard(role)
    )


@router.message(AdminContactTextStates.waiting_text)
async def admin_save_contact_text(message: Message, state: FSMContext):
    if message.text == "⬅️ Orqaga":
        await state.set_state(AdminMenuStates.menu)
        role = await get_admin_role(message.from_user.id)
        await message.answer(
            "🛠 ADMIN PANEL\n\nKerakli bo‘limni tanlang:",
            reply_markup=admin_menu_keyboard(role)
        )
        return
    await db.execute(
        "UPDATE settings SET value = $1 WHERE key = $2",
        message.text,
        "admin_contact_text",
    )

    await state.set_state(AdminMenuStates.menu)

    role = await get_admin_role(message.from_user.id)
    await message.answer(
        "✅ Admin bilan bog‘lanish matni yangilandi",
        reply_markup=admin_menu_keyboard(role)
    )

@router.callback_query(VoucherStates.choosing_quantity, F.data.startswith("v_qty:"))
async def voucher_quantity_selected(callback: CallbackQuery, state: FSMContext):
    _, voucher_id, qty = callback.data.split(":")
    qty = int(qty)

    data = await state.get_data()

    total_price = data["price"] * qty
    total_almaz = data["almaz"] * qty

    # umumiy buyurtma sifatida saqlaymiz
    await state.update_data(
        quantity=qty,
        total_price=total_price,
        total_almaz=total_almaz
    )

    # 🔥 ENDI ALMAZ PAKET BILAN BIR XIL FLOW
    await state.set_state(OrderStates.waiting_ff_id)

    await safe_edit(
        callback,
        "✅ <b>BUYURTMA MA’LUMOTI</b>\n\n"
        f"💳 Voucher: {data['name']}\n"
        f"🧮 Soni: {qty} dona\n"
        f"💎 Jami almaz: {total_almaz}\n"
        f"💰 Jami narx: {total_price:,} so‘m\n\n"
        "⚡ Yetkazish: 5–15 daqiqa\n"
        "🔒 Xavfsiz va kafolatlangan\n\n"
        "🆔 <b>Free Fire ID</b> raqamingizni kiriting:\n"
        "⚠️ <i>Diqqat: noto'g'ri ID jo'natilgan holatlarda Adminga murojaat qilishingiz kerak</i>"
    )


    await callback.answer()


@router.callback_query(F.data == "back_to_vouchers")
async def back_to_vouchers(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await buy_almaz_handler(callback, state)

@router.callback_query(F.data == "buy_voucher")
async def buy_voucher_handler(callback: CallbackQuery, state: FSMContext):
    rows = await db.fetch(
        """
        SELECT id, name, almaz, price
        FROM vouchers
        WHERE active = TRUE
        ORDER BY
            CASE
                WHEN lower(name) LIKE '%oylik%' THEN 0
                WHEN lower(name) LIKE '%haftalik%' THEN 1
                ELSE 2
            END,
            id
        """
    )

    if not rows:
        await callback.answer("❌ Voucherlar mavjud emas", show_alert=True)
        return

    keyboard = []
    for v in rows:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{v['id']}. {v['name']} — {v['price']:,} so‘m",
                callback_data=f"voucher:{v['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_menu")
    ])

    await safe_edit(
        callback,
        "💳 Kerakli voucherni tanlang.\n\n"

        "🎮 Mos keladi • ⚡ Tez ishlaydi • 🔒 Xavfsiz",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("voucher:"))
async def voucher_selected_handler(callback: CallbackQuery, state: FSMContext):
    voucher_id = int(callback.data.split(":")[1])

    voucher = await db.fetchrow(
        "SELECT name, almaz, price FROM vouchers WHERE id = $1 AND active = TRUE",
        voucher_id,
    )

    if not voucher:
        await callback.answer("❌ Voucher topilmadi", show_alert=True)
        return

    name, almaz, price = voucher["name"], voucher["almaz"], voucher["price"]

    # voucher ma’lumotlarini state’ga saqlaymiz
    await state.update_data(
        is_voucher=True,
        voucher_id=voucher_id,
        name=name,
        almaz=almaz,
        price=price
    )

    await state.set_state(VoucherStates.choosing_quantity)

    await safe_edit(
        callback,
        f"{name}\n\n"
        f"💎 {almaz} almaz / 1 dona\n"
        f"💰 {price:,} so‘m / 1 dona\n\n"
        "🧮 Nechta dona olmoqchisiz?",
        reply_markup=voucher_quantity_keyboard(voucher_id)
    )
    await callback.answer()

@router.message(AdminOrdersStates.waiting_order_id)
async def admin_order_detail(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER, ADMIN_ROLE_MAIN, ADMIN_ROLE_VIEWER))
    if not role:
        return

    if message.text == "⬅️ Orqaga":
        await state.set_state(AdminMenuStates.menu)
        role = await get_admin_role(message.from_user.id)
        await message.answer(
            "🛠 ADMIN PANEL",
            reply_markup=admin_menu_keyboard(role)
        )
        return

    if not message.text.isdigit():
        await message.answer("❌ Iltimos, BUYURTMA ID raqamini kiriting")
        return

    order_id = int(message.text)

    order = await db.fetchrow(
        """
        SELECT
            id,
            user_id,
            username,
            first_name,
            product_name,
            almaz,
            quantity,
            price,
            ff_id,
            status,
            created_at,
            admin_id,
            approved_at,
            rejected_at,
            bonus_percent_bp,
            bonus_amount
        FROM orders
        WHERE id = $1
        """,
        order_id,
    )

    if not order:
        await message.answer("❌ Buyurtma topilmadi")
        return

    formatted_date = format_dt_utc5(order["created_at"])
    approved_at = format_dt_utc5(order["approved_at"])
    rejected_at = format_dt_utc5(order["rejected_at"])
    bonus_percent = (order["bonus_percent_bp"] or 0) / 100

    username = order["username"] or "yo‘q"
    text = (
        f"🧾 <b>BUYURTMA #{order['id']}</b>\n\n"
        f"👤 <b>User:</b> {order['first_name']} (@{username})\n"
        f"🆔 <b>Telegram ID:</b> {order['user_id']}\n\n"
        f"📦 <b>Mahsulot:</b> {order['product_name']}\n"
        f"💎 <b>Almaz:</b> {order['almaz']}\n"
        f"🧮 <b>Soni:</b> {order['quantity']}\n"
        f"💰 <b>Narx:</b> {order['price']:,} so‘m\n\n"
        f"🎮 <b>FF ID:</b> {order['ff_id']}\n"
        f"📌 <b>Holat:</b> {order['status']}\n"
        f"🕒 <b>Sana:</b> {formatted_date}\n"
        f"👮 <b>Admin:</b> {order['admin_id'] or '-'}\n"
        f"✅ <b>Tasdiq vaqti (UTC+5):</b> {approved_at}\n"
        f"❌ <b>Rad vaqti (UTC+5):</b> {rejected_at}\n"
        f"🎁 <b>Bonus:</b> {bonus_percent}% | +{order['bonus_amount'] or 0} 💎"
    )

    await message.answer(text)



@router.message(AdminMenuStates.menu, F.text == "🪵 Admin loglari")
async def admin_logs_view(message: Message):
    role = await require_role(message, (ADMIN_ROLE_SUPER, ADMIN_ROLE_MAIN, ADMIN_ROLE_VIEWER))
    if not role:
        return

    logs = await db.fetch(
        """
        SELECT admin_id, action, order_id, details, created_at
        FROM admin_logs
        ORDER BY id DESC
        LIMIT 15
        """
    )

    if not logs:
        await message.answer("🪵 Loglar hozircha yo‘q")
        return

    text = "🪵 ADMIN LOGI (oxirgi 15)\n\n"

    for row in logs:
        admin_id = row["admin_id"]
        action = row["action"]
        order_id = row["order_id"]
        details = row["details"]
        created_at = row["created_at"]
        text += (
            f"👮 Admin ID: {admin_id}\n"
            f"⚙️ Amal: {action}\n"
            f"🆔 Buyurtma: {order_id}\n"
            f"📝 Izoh: {details or '-'}\n"
            f"🕒 {format_dt_utc5(created_at)}\n\n"
        )

    await message.answer(text)

@router.callback_query(F.data == "cancel_process")
async def cancel_process_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id

    # qaysi tur ekanini aniqlaymiz
    order_type = "voucher" if data.get("is_voucher") else "almaz"

    # 🔔 REMINDER YARATAMIZ
    await create_reminder(user_id, order_type)

    await state.clear()

    await callback.message.answer("❌ Xarid jarayoni bekor qilindi.")
    await show_main_menu_callback(callback)
    await callback.answer("Jarayon bekor qilindi")


@router.message(AdminMenuStates.menu, F.text == "🔍 Foydalanuvchini topish")
async def admin_user_search_start(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER, ADMIN_ROLE_MAIN, ADMIN_ROLE_VIEWER))
    if not role:
        return

    await state.set_state(AdminUserSearchStates.waiting_query)

    await message.answer(
        "🔍 <b>FOYDALANUVCHINI TOPISH</b>\n\n"
        "Telegram ID yoki @username yuboring:",
        reply_markup=user_search_back_keyboard()
    )

@router.message(AdminUserSearchStates.waiting_query)
async def admin_user_search_handler(message: Message, state: FSMContext):
    if message.text == "⬅️ Orqaga":
        await state.set_state(AdminMenuStates.menu)
        role = await get_admin_role(message.from_user.id)
        await message.answer(
            "🛠 ADMIN PANEL",
            reply_markup=admin_menu_keyboard(role)
        )
        return

    query = message.text.strip()

    # 🔍 USER TOPISH
    if query.isdigit():
        user = await db.fetchrow(
            "SELECT user_id, first_name, username, joined_at, almaz_balance, bonus_almaz, total_almaz "
            "FROM users WHERE user_id = $1",
            int(query),
        )
    else:
        if query.startswith("@"):
            query = query[1:]
        user = await db.fetchrow(
            "SELECT user_id, first_name, username, joined_at, almaz_balance, bonus_almaz, total_almaz "
            "FROM users WHERE username = $1",
            query,
        )

    if not user:
        await message.answer("❌ Foydalanuvchi topilmadi")
        return

    (
        user_id,
        first_name,
        username,
        joined_at,
        almaz_balance,
        bonus_almaz,
        total_almaz
    ) = user

    # 🧾 BUYURTMALAR STATISTIKASI
    stats_row = await db.fetchrow(
        """
        SELECT
            COUNT(*) AS total_orders,
            SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) AS approved_orders,
            SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) AS rejected_orders,
            MAX(created_at) AS last_order_date,
            COALESCE(SUM(CASE WHEN status = 'approved' THEN price ELSE 0 END), 0) AS total_spent
        FROM orders
        WHERE user_id = $1
        """,
        user_id,
    )
    total_orders = stats_row["total_orders"]
    approved_orders = stats_row["approved_orders"] or 0
    rejected_orders = stats_row["rejected_orders"] or 0
    last_order_date = stats_row["last_order_date"]
    total_spent = stats_row["total_spent"]

    # 📦 OXIRGI 5 BUYURTMA
    last_orders = await db.fetch(
        """
        SELECT product_name, almaz, price, created_at
        FROM orders
        WHERE user_id = $1 AND status = 'approved'
        ORDER BY created_at DESC
        LIMIT 5
        """,
        user_id,
    )

    joined_dt = format_dt_utc5(joined_at).split(" | ")[0]

    text = (
        f"👤 <b>FOYDALANUVCHI PROFILI</b>\n\n"
        f"👤 Ism: {first_name}\n"
        f"🔗 Username: @{username if username else 'yo‘q'}\n"
        f"🆔 Telegram ID: {user_id}\n"
        f"📅 Botga kirgan: {joined_dt}\n\n"
        f"📊 <b>STATISTIKA</b>\n"
        f"🧾 Jami buyurtmalar: {total_orders}\n"
        f"✅ Tasdiqlangan: {approved_orders}\n"
        f"❌ Rad etilgan: {rejected_orders}\n"
        f"💰 Jami sarflangan: {total_spent:,} so‘m\n\n"
        f"💎 <b>BALANS</b>\n"
        f"💎 Joriy: {almaz_balance}\n"
        f"🎁 Bonus: {bonus_almaz}\n"
        f"📦 Jami olingan: {total_almaz}\n"
    )

    if last_orders:
        text += "\n📦 <b>OXIRGI 5 SOTIB OLINGAN</b>\n"
        for row in last_orders:
            name = row["product_name"]
            almaz = row["almaz"]
            price = row["price"]
            created_at = row["created_at"]
            date_fmt = format_dt_utc5(created_at).split(" | ")[0]
            text += f"• {name} | 💎 {almaz} | 💰 {price:,} so‘m | {date_fmt}\n"

    await message.answer(text)

@router.message(AdminMenuStates.menu, F.text == "💳 Voucherlar")
async def admin_vouchers_menu(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    await push_nav(state, "admin_vouchers")
    await show_admin_vouchers_menu(message, state)

@router.message(AdminVouchersStates.menu, F.text == "✏️ Voucher tahrirlash")
async def admin_edit_voucher_start(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    vouchers = await db.fetch(
        """
        SELECT id, name
        FROM vouchers
        WHERE active = TRUE
        ORDER BY
            CASE
                WHEN lower(name) LIKE '%oylik%' THEN 0
                WHEN lower(name) LIKE '%haftalik%' THEN 1
                ELSE 2
            END,
            id
        """
    )

    if not vouchers:
        await message.answer("❌ Voucherlar topilmadi")
        return

    text = "✏️ Tahrirlash uchun voucher RAQAMINI yuboring:\n\n"
    for v in vouchers:
        text += f"{v['id']}. {v['name']}\n"

    await state.set_state(AdminVouchersStates.edit_select)
    await message.answer(text)

@router.message(AdminVouchersStates.edit_select)
async def admin_edit_voucher_choose(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    if not message.text.isdigit():
        await message.answer("❌ Voucher ID raqam bo‘lishi kerak")
        return

    voucher_id = int(message.text)

    row = await db.fetchrow(
        "SELECT id FROM vouchers WHERE id = $1 AND active = TRUE",
        voucher_id,
    )
    if not row:
        await message.answer("❌ Voucher topilmadi")
        return

    await state.update_data(voucher_id=voucher_id)
    await state.set_state(AdminVouchersStates.edit_field)

    await message.answer(
        "Qaysi maydonni o‘zgartiramiz?\n\n"
        "1 — Nomi\n"
        "2 — Almaz miqdori\n"
        "3 — Narxi"
    )

@router.message(AdminVouchersStates.edit_field)
async def admin_edit_voucher_field(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    if message.text not in ["1", "2", "3"]:
        await message.answer("❌ 1, 2 yoki 3 ni tanlang")
        return

    field_map = {
        "1": "name",
        "2": "almaz",
        "3": "price"
    }

    await state.update_data(field=field_map[message.text])
    await state.set_state(AdminVouchersStates.edit_value)

    await message.answer("✍️ Yangi qiymatni kiriting:")

@router.message(AdminVouchersStates.edit_value)
async def admin_edit_voucher_save(message: Message, state: FSMContext):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    data = await state.get_data()

    field = data["field"]
    voucher_id = data["voucher_id"]
    value = message.text

    if field in ["almaz", "price"] and not value.isdigit():
        await message.answer("❌ Faqat raqam kiriting")
        return

    await db.execute(
        f"UPDATE vouchers SET {field} = $1 WHERE id = $2",
        value,
        voucher_id,
    )

    await state.set_state(AdminVouchersStates.menu)

    await message.answer(
        "✅ Voucher muvaffaqiyatli yangilandi",
        reply_markup=admin_vouchers_menu_keyboard()
    )


@router.message(AdminVouchersStates.edit_select, F.text == "⬅️ Orqaga")
@router.message(AdminVouchersStates.edit_field, F.text == "⬅️ Orqaga")
@router.message(AdminVouchersStates.edit_value, F.text == "⬅️ Orqaga")
async def admin_vouchers_edit_back(message: Message, state: FSMContext):
    await state.set_state(AdminVouchersStates.menu)
    await message.answer(
        "💳 VOUCHERLAR BOSHQARUVI",
        reply_markup=admin_vouchers_menu_keyboard()
    )

@router.message(AdminVouchersStates.menu, F.text == "⬅️ Orqaga")
async def admin_vouchers_back(message: Message, state: FSMContext):
    await state.set_state(AdminMenuStates.menu)

    role = await get_admin_role(message.from_user.id)
    await message.answer(
        "🛠 ADMIN PANEL",
        reply_markup=admin_menu_keyboard(role)
    )

async def reminder_worker(bot):
    print("🔔 Reminder worker ishga tushdi")

    while True:
        try:
            now = utc_now()

            reminders = await db.fetch(
                """
                SELECT id, user_id, type
                FROM reminders
                WHERE sent = FALSE AND send_at <= $1
                """,
                now,
            )

            if reminders:
                print(f"🔔 Topildi: {len(reminders)} ta reminder")

            for row in reminders:
                reminder_id = row["id"]
                user_id = row["user_id"]
                r_type = row["type"]
                try:
                    if r_type == "voucher":
                        text = (
                            "💳 <b>Bugun voucher sotib olishni unutdingizmi?</b>\n\n"
                            "⏳ Aksiyalar cheklangan.\n"
                            "🎁 Qulay paytda davom etishingiz mumkin."
                        )
                    else:
                        text = (
                            "💎 <b>Bugun almaz sotib olishni unutdingizmi?</b>\n\n"
                            "🎮 Free Fire sizni kutyapti!\n"
                            "⚡ 5–60 daqiqada yetkazib beramiz."
                        )

                    await bot.send_message(user_id, text)

                    await db.execute(
                        "UPDATE reminders SET sent = TRUE WHERE id = $1",
                        reminder_id,
                    )

                    print(f"✅ Reminder yuborildi → user {user_id}")

                except Exception as e:
                    print("❌ Reminder yuborishda xato:", e)

                    await db.execute(
                        "UPDATE reminders SET sent = TRUE WHERE id = $1",
                        reminder_id,
                    )

        except Exception as e:
            print("❌ Reminder worker error:", e)

        await asyncio.sleep(10)  # 🔥 TEST UCHUN 10 SONIYA


async def bonus_code_worker(bot):
    print("🎁 Bonus code worker ishga tushdi")

    while True:
        try:
            now = utc_now()
            rows = await db.fetch(
                """
                SELECT id, owner_id, code, total_uses, total_bonus
                FROM bonus_codes
                WHERE expires_at <= $1 AND expired_notified = FALSE
                """,
                now,
            )

            for row in rows:
                await db.execute(
                    """
                    UPDATE bonus_codes
                    SET active = FALSE, expired_notified = TRUE
                    WHERE id = $1
                    """,
                    row["id"],
                )

                try:
                    await bot.send_message(
                        row["owner_id"],
                        "⏰ <b>BONUS KOD MUDDATI TUGADI</b>\n\n"
                        f"🎁 Kod: <code>{row['code']}</code>\n"
                        f"👥 Ishlatilgan: {row['total_uses']} ta\n"
                        f"💎 Jami bonus: {row['total_bonus']} 💎\n\n"
                        "✅ Endi yangi kod yaratishingiz mumkin."
                    )
                except Exception:
                    pass

        except Exception as e:
            print("❌ Bonus code worker error:", e)

        await asyncio.sleep(60)

@router.callback_query(F.data == "enter_promocode")
async def enter_promocode_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PromoCodeStates.waiting_code)

    await safe_edit(
        callback,
        "🎁 <b>PROMOKOD KIRITISH</b>\n\n"
        "Promokod — bu bonus almaz olish imkoniyati.\n"
        "To‘g‘ri promokod kiritilsa, balansingizga "
        "qo‘shimcha 💎 bonus beriladi.\n\n"
        "✍️ <b>Promokod so‘zini kiriting</b>\n"
        "Masalan: <code>ZONIKSBB</code>",
        reply_markup=promocode_back_to_menu_keyboard()
    )

    await callback.answer()

@router.message(PromoCodeStates.waiting_code)
async def apply_promocode_handler(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    user_id = message.from_user.id
    now = utc_now()

    # 🔒 ANTI-ABUSE: user nechta promo ishlatganini tekshiramiz
    row = await db.fetchrow(
        "SELECT promo_used FROM users WHERE user_id = $1",
        user_id,
    )

    promo_used = row["promo_used"] if row else 0

    if promo_used >= 3:
        await message.answer(
            "⚠️ Siz juda ko‘p promokod ishlatgansiz.\n\n"
            "Keyingi promokodlardan foydalanish uchun xarid qilish kerak bo‘ladi."
        )
        return

    # 🔍 PROMOKODNI TEKSHIRAMIZ
    promo = await db.fetchrow(
        """
        SELECT id, almaz_reward, max_uses, used_count, expires_at, active
        FROM promocodes
        WHERE code = $1 AND is_deleted = FALSE
        """,
        code,
    )

    if not promo:
        await message.answer("❌ Bunday promokod mavjud emas")
        return

    promo_id = promo["id"]
    almaz = promo["almaz_reward"]
    max_uses = promo["max_uses"]
    used_count = promo["used_count"]
    expires_at = promo["expires_at"]
    active = promo["active"]

    if not active:
        await message.answer("⛔ Bu promokod faol emas")
        return

    if expires_at and now > expires_at:
        await message.answer("⏰ Promokod muddati tugagan")
        return

    if used_count >= max_uses:
        await message.answer("😔 Afsus, promokod limiti tugagan")
        return

    # 👤 USER OLDIN ISHLATGANMI?
    row = await db.fetchrow(
        "SELECT 1 FROM promocode_uses WHERE promocode_id = $1 AND user_id = $2",
        promo_id,
        user_id,
    )
    if row:
        await message.answer("⚠️ Siz bu promokodni allaqachon ishlatgansiz")
        return

    # ✅ HAMMASI TO‘G‘RI — ALMAZ QO‘SHAMIZ
    await db.execute(
        """
        UPDATE users
        SET 
            almaz_balance = almaz_balance + $1,
            total_almaz = total_almaz + $1,
            promo_used = promo_used + 1
        WHERE user_id = $2
        """,
        almaz,
        user_id,
    )

    await db.execute(
        """
        UPDATE promocodes
        SET used_count = used_count + 1
        WHERE id = $1
        """,
        promo_id,
    )

    await db.execute(
        """
        INSERT INTO promocode_uses (promocode_id, user_id, used_at)
        VALUES ($1, $2, $3)
        """,
        promo_id,
        user_id,
        now,
    )

    await state.clear()

    await message.answer(
        f"🎉 <b>PROMOKOD MUVAFFAQIYATLI!</b>\n\n"
        f"🎁 +{almaz} 💎 almaz balansingizga qo‘shildi\n"
        f"🔥 Balansingiz yangilandi!"
    )


@router.message(AdminPromoStates.menu, F.text == "📊 Promokodlar ro‘yxati")
async def admin_promo_list(message: Message):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    rows = await db.fetch(
        """
        SELECT code, used_count, max_uses, active, is_deleted, expires_at, almaz_reward
        FROM promocodes
        WHERE is_deleted = FALSE
        ORDER BY id DESC
        LIMIT 10
        """
    )

    if not rows:
        await message.answer("📭 Promokodlar yo‘q")
        return

    text = "📊 <b>PROMOKODLAR</b>\n\n"

    for row in rows:
        code = row["code"]
        used = row["used_count"]
        max_u = row["max_uses"]
        active = row["active"]
        is_deleted = row["is_deleted"]
        expires_at = row["expires_at"]
        if is_deleted:
            status = "❌ DELETED"
        elif expires_at and utc_now() > expires_at:
            status = "⏰ EXPIRED"
        else:
            status = "🟢 ACTIVE" if active else "🔴 OFF"
        text += (
            f"{status}\n"
            f"🎁 {code}\n"
            f"📊 {used}/{max_u}\n"
            f"💎 Almaz: {row['almaz_reward']}\n\n"
        )

    buttons = []
    for row in rows:
        buttons.append([InlineKeyboardButton(text=f"❌ O‘chirish {row['code']}", callback_data=f"promo_del:{row['code']}")])

    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
    )


@router.message(AdminPromoStates.menu, F.text == "⬅️ Orqaga")
async def admin_promo_back(message: Message, state: FSMContext):
    await state.set_state(AdminMenuStates.menu)
    role = await get_admin_role(message.from_user.id)
    await message.answer(
        "🛠 ADMIN PANEL",
        reply_markup=admin_menu_keyboard(role)
    )

@router.callback_query(F.data.startswith("promo_del:"))
async def admin_promocode_delete_prompt(callback: CallbackQuery):
    role = await get_admin_role(callback.from_user.id)
    if role not in (ADMIN_ROLE_SUPER,):
        await callback.answer("⛔ Sizda ruxsat yo‘q", show_alert=True)
        return
    code = callback.data.split(":", 1)[1].strip().upper()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ha, o‘chirish", callback_data=f"promo_del_yes:{code}"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"promo_del_no:{code}"),
            ]
        ]
    )
    await callback.message.answer(
        f"Rostdan ham <b>{code}</b> promokodni o‘chirmoqchimisiz?",
        reply_markup=kb
    )
    await callback.answer()


@router.callback_query(F.data.startswith("promo_del_yes:"))
async def admin_promocode_delete_confirm(callback: CallbackQuery):
    role = await get_admin_role(callback.from_user.id)
    if role not in (ADMIN_ROLE_SUPER,):
        await callback.answer("⛔ Sizda ruxsat yo‘q", show_alert=True)
        return
    code = callback.data.split(":", 1)[1].strip().upper()
    await db.execute(
        "UPDATE promocodes SET is_deleted = TRUE, active = FALSE WHERE code = $1",
        code,
    )
    await callback.message.answer(f"⛔ Promokod <b>{code}</b> o‘chirildi")
    await callback.answer()


@router.callback_query(F.data.startswith("promo_del_no:"))
async def admin_promocode_delete_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Bekor qilindi")
    await admin_promo_list(callback.message)

@router.message(AdminPromoStates.menu, F.text.startswith("👥 Kim ishlatdi "))
async def admin_promo_users(message: Message):
    role = await require_role(message, (ADMIN_ROLE_SUPER,))
    if not role:
        return

    code = message.text.replace("👥 Kim ishlatdi ", "").strip().upper()

    rows = await db.fetch(
        """
        SELECT u.user_id, u.first_name, u.username, pu.used_at
        FROM promocode_uses pu
        JOIN promocodes p ON p.id = pu.promocode_id
        JOIN users u ON u.user_id = pu.user_id
        WHERE p.code = $1
        ORDER BY pu.used_at DESC
        """,
        code,
    )

    if not rows:
        await message.answer("📭 Hech kim ishlatmagan")
        return

    text = f"👥 <b>{code}</b> promokodini ishlatganlar:\n\n"

    for row in rows:
        uid = row["user_id"]
        name = row["first_name"]
        username = row["username"]
        used_at = row["used_at"]
        date_fmt = format_dt_utc5(used_at)
        text += f"• {name} (@{username}) — {date_fmt}\n"

    await message.answer(text)

BONUS_CODE_HELP_TEXT = (
    "📘 <b>BONUSLI KOD — TO‘LIQ QO‘LLANMA</b>\n\n"

    "Bonusli kod tizimi sizga do‘stlaringiz bilan birga "
    "foydaliroq donat qilish imkonini beradi.\n"
    "Tizim oddiy, shaffof va avtomatik ishlaydi.\n\n"

    "━━━━━━━━━━━━━━\n"
    "👤 <b>1-QADAM. BONUS KOD YARATISH</b>\n"
    "━━━━━━━━━━━━━━\n"
    "• «🎁 Kod yaratish» tugmasini bosing\n"
    "• Sizga maxsus bonus kod beriladi\n"
    "• Har bir foydalanuvchida faqat 1 ta aktiv kod bo‘ladi\n"
    "• Kod 4 kun davomida amal qiladi\n\n"

    "━━━━━━━━━━━━━━\n"
    "🤝 <b>2-QADAM. KODNI DO‘STLARGA BERISH</b>\n"
    "━━━━━━━━━━━━━━\n"
    "• Yaratilgan kodni do‘stlaringizga yuboring\n"
    "• Do‘stlaringiz «📥 Kod ishlatish» tugmasi orqali kodni kiritadi\n"
    "• Shundan so‘ng ular odatdagidek paket yoki voucher sotib olishadi\n\n"

    "━━━━━━━━━━━━━━\n"
    "🎁 <b>3-QADAM. BONUS OLISH</b>\n"
    "━━━━━━━━━━━━━━\n"
    "• Do‘stingiz xarid qilgach, u bonus oladi\n"
    "• Siz ham har bir xariddan bonus olasiz\n"
    "• Bir kod qancha ko‘p ishlatilsa, bonus foizi shuncha foydaliroq bo‘ladi\n\n"

    "━━━━━━━━━━━━━━\n"
    "📈 <b>BONUS QANDAY HISOBLANADI?</b>\n"
    "━━━━━━━━━━━━━━\n"
    "• Bonus foizi foydalanish soniga qarab oshib boradi\n"
    "• Bonus almaz sifatida balansga qo‘shiladi\n"
    "• Bonuslar avtomatik va xatosiz hisoblanadi\n\n"

    "━━━━━━━━━━━━━━\n"
    "🔁 <b>BONUS SIKLI</b>\n"
    "━━━━━━━━━━━━━━\n"
    "• Bonuslar 5 kunlik sikl asosida ishlaydi\n"
    "• 5 kun o‘tgach, hisob qaytadan boshlanadi\n"
    "• Bu sizga doimiy bonus yig‘ish imkonini beradi\n\n"

    "━━━━━━━━━━━━━━\n"
    "🔒 <b>MUHIM QOIDALAR</b>\n"
    "━━━━━━━━━━━━━━\n"
    "• O‘zingiz yaratgan kodni o‘zingiz ishlata olmaysiz\n"
    "• Har bir xarid real va avtomatik tekshiriladi\n"
    "• Kod faqat faol bo‘lgan vaqtda ishlaydi\n"
    "• Barcha jarayon shaffof va adolatli\n\n"

    "━━━━━━━━━━━━━━\n"
    "💡 <b>NIMA YUTASIZ?</b>\n"
    "━━━━━━━━━━━━━━\n"
    "• Arzonroq donat\n"
    "• Qo‘shimcha bonus almazlar\n"
    "• Do‘stlaringiz uchun ham foyda\n\n"

    "<b>Bu shunchaki aksiya emas — bu foydali tizim.</b>"
)



@router.callback_query(F.data == "bonus_code_help")
async def bonus_code_help_handler(callback: CallbackQuery):
    back_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="bonus_code_menu"
                )
            ]
        ]
    )

    await safe_edit(
        callback,
        BONUS_CODE_HELP_TEXT,
        reply_markup=back_keyboard
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    await safe_edit(
        callback,
        MAIN_MENU_TEXT,
        reply_markup=main_menu_keyboard()
    )

    await callback.answer()
