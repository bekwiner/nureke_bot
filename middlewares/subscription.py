from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any

from handlers import check_subscription, sub_required_markup


class SubscriptionMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable,
        event,
        data: Dict[str, Any]
    ):

        # faqat message yoki callback ishlaydi
        user = None
        chat = None

        if isinstance(event, Message):
            user = event.from_user
            chat = event.chat
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            chat = event.message.chat

        if not user or not chat:
            return await handler(event, data)

        # faqat private chat
        if chat.type != "private":
            return await handler(event, data)

        # kanal tekshiruv
        not_sub = await check_subscription(user.id)

        if not_sub:

            text = (
                "🔒 <b>Botdan foydalanish uchun kanallarga obuna bo‘ling</b>\n\n"
                "Obuna bo‘lgach <b>✅ Tekshirish</b> tugmasini bosing."
            )

            if isinstance(event, Message):
                await event.answer(
                    text,
                    parse_mode="HTML",
                    reply_markup=sub_required_markup(not_sub)
                )

            elif isinstance(event, CallbackQuery):
                await event.message.answer(
                    text,
                    parse_mode="HTML",
                    reply_markup=sub_required_markup(not_sub)
                )

            return

        return await handler(event, data)