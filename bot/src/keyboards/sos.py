from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

all_right_message = "✅ Все верно"
cancel_message = "🚫 Отменить"


def confirmation_kb() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text=all_right_message), KeyboardButton(text=cancel_message)]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons)


def operator_request_kb(request_id: str) -> InlineKeyboardMarkup:
    # callback_data до 64 байт; префикс + UUID (36) = 50 символов
    buttons = [
        [InlineKeyboardButton(text="✅ Принять", callback_data=f"accept:{request_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
