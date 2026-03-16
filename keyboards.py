# -*- coding: utf-8 -*-
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard(extra_buttons: list[str] | None = None):
    keyboard = [
        [
            KeyboardButton(text="💎 Almaz olish"),
            KeyboardButton(text="🎫 Voucher olish")
        ],
        [
            KeyboardButton(text="📊 Paket narxlari"),
            KeyboardButton(text="💰 Mening balansim")
        ],
        [
            KeyboardButton(text="📞 Yordam / Admin")
        ],
    ]

    for label in extra_buttons or []:
        cleaned = (label or "").strip()
        if cleaned:
            keyboard.append([KeyboardButton(text=cleaned)])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def confirm_package_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="back_to_packages"
                ),
                InlineKeyboardButton(
                    text="💳 To‘lov qilish",
                    callback_data="go_to_payment"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💰 Sum balansdan yechib olish",
                    callback_data="pay_with_money_balance"
                )
            ],
        ]
    )


def admin_balance_topup_keyboard(request_id: int, user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data=f"topup_confirm:{request_id}:{user_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data=f"topup_cancel:{request_id}:{user_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💣 Soxta chek",
                    callback_data=f"topup_fake:{request_id}:{user_id}"
                )
            ],
        ]
    )

def admin_order_keyboard(user_id: int, almaz: int, order_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlandi",
                    callback_data=f"admin_confirm:{order_id}:{user_id}:{almaz}"
                ),
                InlineKeyboardButton(
                    text="💣 Soxta chek",
                    callback_data=f"admin_fake:{order_id}:{user_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data=f"admin_cancel:{order_id}:{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✍️ Tahrirlash",
                    callback_data=f"admin_edit:{order_id}:{user_id}"
                )
            ]
        ]
    )


def admin_order_edit_keyboard(order_id: int, user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💎 Almaz",
                    callback_data=f"admin_edit_field:{order_id}:{user_id}:almaz"
                ),
                InlineKeyboardButton(
                    text="💰 Narx",
                    callback_data=f"admin_edit_field:{order_id}:{user_id}:price"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎮 FF ID",
                    callback_data=f"admin_edit_field:{order_id}:{user_id}:ff_id"
                ),
                InlineKeyboardButton(
                    text="📦 Nomi",
                    callback_data=f"admin_edit_field:{order_id}:{user_id}:product_name"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Bekor",
                    callback_data=f"admin_edit_cancel:{order_id}:{user_id}"
                )
            ],
        ]
    )


def admin_order_edit_cancel_keyboard(order_id: int, user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="↩️ Bekor",
                    callback_data=f"admin_edit_cancel:{order_id}:{user_id}"
                )
            ]
        ]
    )


from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def admin_menu_keyboard(role: str):
    role = (role or "").lower()

    if role == "viewer":
        keyboard = [
            [KeyboardButton(text="👥 Foydalanuvchilar soni")],
            [KeyboardButton(text="🧾 Buyurtmalar")],
            [KeyboardButton(text="🪵 Admin loglari")],
            [KeyboardButton(text="⬅️ Orqaga")],
        ]
    elif role == "main_admin":
        keyboard = [
            [KeyboardButton(text="🧾 Buyurtmalar")],
            [KeyboardButton(text="Admins statics")],
            [KeyboardButton(text="Asosiy menyu textini o'zgartirish")],
            [KeyboardButton(text="📥 Bo'limga yuklash")],
            [KeyboardButton(text="🪵 Admin loglari")],
            [KeyboardButton(text="🔍 Foydalanuvchini topish")],
            [KeyboardButton(text="⬅️ Orqaga")],
        ]
    else:
        keyboard = [
            [KeyboardButton(text="👥 Foydalanuvchilar soni")],
            [KeyboardButton(text="🧾 Buyurtmalar")],
            [KeyboardButton(text="📦 Paketlar")],
            [KeyboardButton(text="💳 Voucherlar")],
            [KeyboardButton(text="📊 Daromad statistikasi")],
            [KeyboardButton(text="Admins statics")],
            [KeyboardButton(text="Asosiy menyu textini o'zgartirish")],
            [KeyboardButton(text="📥 Bo'limga yuklash")],
            [KeyboardButton(text="🪵 Admin loglari")],
            [KeyboardButton(text="🧩 Majburiy kanallar")],
            [KeyboardButton(text="🎁 Promokodlar")],
            [KeyboardButton(text="🔍 Foydalanuvchini topish")],
            [KeyboardButton(text="💰 Narxlar matnini tahrirlash")],
            [KeyboardButton(text="📞 Admin bilan bog‘lanish matni")],
            [KeyboardButton(text="🖼 Asosiy menyu rasmi")],
            [KeyboardButton(text="📣 Reklama / Xabar")],
            [KeyboardButton(text="💳 To‘lov kartalari")],
            [KeyboardButton(text="📌 Kanal ulash")],
            [KeyboardButton(text="👮‍♂️ Adminlar")],
            [KeyboardButton(text="⬅️ Orqaga")],
        ]

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)



def remove_keyboard():
    return ReplyKeyboardRemove()

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def prices_back_inline():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="prices_back"
                )
            ]
        ]
    )

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def dynamic_packages_keyboard(packages: list):
    keyboard = []

    for pkg in packages:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{pkg['name']} – {pkg['price']:,} so‘m",
                callback_data=f"buy_pkg:{pkg['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="back_to_menu"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_packages_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Paket qo‘shish")],
            [KeyboardButton(text="✏️ Paket tahrirlash")],
            [KeyboardButton(text="❌ Paket o‘chirish")],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )




def voucher_quantity_keyboard(voucher_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1️⃣", callback_data=f"v_qty:{voucher_id}:1"),
                InlineKeyboardButton(text="2️⃣", callback_data=f"v_qty:{voucher_id}:2"),
                InlineKeyboardButton(text="3️⃣", callback_data=f"v_qty:{voucher_id}:3"),
            ],
            [
                InlineKeyboardButton(text="4️⃣", callback_data=f"v_qty:{voucher_id}:4"),
                InlineKeyboardButton(text="5️⃣", callback_data=f"v_qty:{voucher_id}:5"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Orqaga", callback_data="buy_voucher")
            ]
        ]
    )

def cancel_process_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Jarayonni bekor qilish",
                    callback_data="cancel_process"
                )
            ]
        ]
    )

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def orders_back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )

def user_search_back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )

def admin_vouchers_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✏️ Voucher tahrirlash")],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )

def promo_enter_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎁 Promokodni ishlatish",
                    callback_data="enter_promocode"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📃 Balansdagi almazni yechish",
                    callback_data="withdraw_start"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 TO‘LOV BOSQICHI",
                    callback_data="balance_payment_stage"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="back_to_menu"
                )
            ]
        ]
    )


def balance_payment_stage_back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="balance"
                )
            ]
        ]
    )


def admin_promocode_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Promokod yaratish")],
            [KeyboardButton(text="📊 Promokodlar ro‘yxati")],
            [KeyboardButton(text="⬅️ Orqaga")]
        ],
        resize_keyboard=True
    )


def promo_input_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True
    )


def back_only_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Orqaga")],
        ],
        resize_keyboard=True
    )


def bonus_code_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Kod yaratish", callback_data="bonus_code_create")],
            [InlineKeyboardButton(text="🎁 Koddan foydalanish", callback_data="bonus_code_use")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_menu")],
        ]
    )


def bonus_code_buy_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💎 Almaz paketlar", callback_data="bonus_buy_almaz")],
            [InlineKeyboardButton(text="💳 Voucherlar", callback_data="bonus_buy_voucher")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="bonus_code_menu")],
        ]
    )


def admin_broadcast_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Matn")],
            [KeyboardButton(text="🖼 Rasm")],
            [KeyboardButton(text="🎥 Video")],
            [KeyboardButton(text="🎵 Musiqa")],
            [KeyboardButton(text="📎 Fayl")],
            [KeyboardButton(text="📊 So‘rovnoma")],
            [KeyboardButton(text="⬅️ Orqaga")],
        ],
        resize_keyboard=True
    )


def broadcast_confirm_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Yuborish", callback_data="broadcast_send"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="broadcast_cancel"),
            ]
        ]
    )


def admin_roles_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Admin qo'shish")],
            [KeyboardButton(text="✏️ Admin roli")],
            [KeyboardButton(text="❌ Admin o'chirish")],
            [KeyboardButton(text="⬅️ Orqaga")],
        ],
        resize_keyboard=True
    )


def admin_payment_cards_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Karta qo'shish")],
            [KeyboardButton(text="✏️ Karta tahrirlash")],
            [KeyboardButton(text="✅ Aktiv qilish")],
            [KeyboardButton(text="🚫 Aktivni o'chirish")],
            [KeyboardButton(text="❌ Karta o'chirish")],
            [KeyboardButton(text="⬅️ Orqaga")],
        ],
        resize_keyboard=True
    )


def admin_logchat_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔗 Kanal username o'rnatish")],
            [KeyboardButton(text="✅ Yoqish/O'chirish")],
            [KeyboardButton(text="🧪 Test yuborish")],
            [KeyboardButton(text="⬅️ Orqaga")],
        ],
        resize_keyboard=True
    )

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def bonus_code_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎁 Kod yaratish",
                    callback_data="bonus_code_create"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📥 Kod ishlatish",
                    callback_data="bonus_code_use"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📘 Qanday ishlaydi?",
                    callback_data="bonus_code_help"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="back_to_menu"
                )
            ]
        ]
    )


def promocode_back_to_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Asosiy menyuga qaytish",
                    callback_data="back_to_main_menu"
                )
            ]
        ]
    )

def admin_stats_admins_keyboard(admins: list[dict]):
    keyboard = []
    for row in admins:
        keyboard.append([
            InlineKeyboardButton(
                text=row["label"],
                callback_data=f"admin_stats_select:{row['user_id']}"
            )
        ])
    keyboard.append([
        InlineKeyboardButton(
            text="Orqaga",
            callback_data="admin_stats_back_menu"
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def admin_stats_detail_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Orqaga", callback_data="admin_stats_back")]
        ]
    )


def main_menu_text_back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Orqaga")]],
        resize_keyboard=True
    )


def admin_content_buttons_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Yangi qo'shish")],
            [KeyboardButton(text="📋 Ro'yxat")],
            [KeyboardButton(text="✏️ Tahrirlash")],
            [KeyboardButton(text="❌ O'chirish")],
            [KeyboardButton(text="⬅️ Orqaga")],
        ],
        resize_keyboard=True,
    )
