"""Клавиатуры для оплаты доступа."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo


def pay_kb() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой оплаты через Telegram Payments."""
    buttons = [
        [InlineKeyboardButton(text='💳 Оплатить', callback_data='pay')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def yoomoney_pay_kb(payment_url: str) -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой оплаты через YooMoney и проверкой."""
    buttons = [
        [InlineKeyboardButton(text='💳 Оплатить через YooMoney', url=payment_url)],
        [InlineKeyboardButton(text='✅ Я оплатил', callback_data='yoomoney_check')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def main_menu_kb(is_paid: bool = False) -> InlineKeyboardMarkup:
    """Главное меню пользователя."""
    buttons = []
    if not is_paid:
        buttons.append([InlineKeyboardButton(text='💳 Оплатить доступ к каналу', callback_data='pay_access')])
    buttons.append([InlineKeyboardButton(text='🆘 Задать вопрос', callback_data='sos')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def restore_start_kb() -> InlineKeyboardMarkup:
    """Начальная клавиатура восстановления доступа."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🔄 Восстановить доступ', callback_data='applied_to_channel')],
            [InlineKeyboardButton(text='🆘 Задать вопрос', callback_data='sos')],
        ]
    )


def restore_invite_kb(invite_link: str) -> InlineKeyboardMarkup:
    """Клавиатура для подачи заявки в канал."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='📢 Подать заявку', url=invite_link)],
        ]
    )


def one_time_channel_invite_kb(invite_link: str) -> InlineKeyboardMarkup:
    """Клавиатура с одноразовой ссылкой для вступления в канал."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🔗 Перейти в канал', url=invite_link)],
        ]
    )
