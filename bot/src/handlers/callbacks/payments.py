"""Обработчики callbacks для оплаты доступа и главного меню."""

import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, PreCheckoutQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.fsm.context import FSMContext

from src.services.payment_service import PaymentService
from src.services.subscription_service import SubscriptionService
from src.keyboards.payment import pay_kb, one_time_channel_invite_kb
from src.states.sos_states import SosStates
from src.utils.config import settings

router = Router()
_payment = PaymentService()
_sub_service = SubscriptionService()

logger = logging.getLogger(__name__)


@router.callback_query(F.data == 'pay_access')
async def show_payment_description(callback: CallbackQuery):
    """Показать описание услуги и выбор способа оплаты."""
    price_text = f'{settings.PAYMENT_PRICE_RUB}₽'

    text = (
        f'💳 <b>Доступ к закрытому каналу</b>\n\n'
        f'Одноразовая оплата за <b>бессрочный</b> доступ.\n\n'
        f'✅ Полный доступ ко всем материалам\n'
        f'✅ Без ежемесячных платежей\n\n'
        f'💰 Стоимость: <b>{price_text}</b>\n\n'
        f'Выберите способ оплаты:'
    )

    # Формируем кнопки в зависимости от доступных методов оплаты
    buttons = []
    if settings.is_payment_enabled:
        buttons.append([InlineKeyboardButton(text='💳 Telegram Payments', callback_data='pay')])
    if settings.is_yoomoney_enabled:
        buttons.append([InlineKeyboardButton(text='💳 YooMoney', callback_data='pay_yoomoney')])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == 'sos')
async def start_sos_callback(callback: CallbackQuery, state: FSMContext):
    """Начать SOS-запрос."""
    await callback.message.answer(text='Подробно опишите вашу проблему')
    await state.set_state(SosStates.confirmation)
    await callback.answer()


@router.callback_query(F.data == 'pay')
async def initiate_payment(callback: CallbackQuery):
    """Отправить инвойс при нажатии кнопки «Оплатить»."""
    logger.info('initiate_payment called: user=%s', callback.from_user.id)
    try:
        await _payment.send_invoice(callback.bot, callback.from_user.id)
        await callback.answer('Счёт выставлен. Проверьте форму оплаты.')
        logger.info('initiate_payment completed: user=%s', callback.from_user.id)
    except ValueError as e:
        logger.error('PAYMENT_TOKEN not configured: %s', e)
        await callback.answer(
            'Оплата временно недоступа. Попробуйте YooMoney или обратитесь к администратору.',
            show_alert=True
        )
    except Exception as e:
        logger.exception('Ошибка при создании счёта: %s', e)
        await callback.answer('Не удалось создать счёт. Попробуйте позже.', show_alert=True)


@router.pre_checkout_query(F.invoice_payload.startswith('user_'))
async def on_pre_checkout(pre_checkout: PreCheckoutQuery):
    """Проверка перед оплатой Telegram Payments — подтверждаем."""
    logger.info('pre_checkout_query received: payload=%s, user=%s',
                pre_checkout.invoice_payload, pre_checkout.from_user.id)
    try:
        await pre_checkout.answer(ok=True)
        logger.info('pre_checkout answered OK')
    except Exception as e:
        logger.exception('Error answering pre_checkout: %s', e)


@router.pre_checkout_query()
async def on_pre_checkout_fallback(pre_checkout: PreCheckoutQuery):
    """Резервный обработчик для всех остальных pre_checkout запросов."""
    logger.warning('Unhandled pre_checkout_query: payload=%s, user=%s',
                   pre_checkout.invoice_payload, pre_checkout.from_user.id)
    try:
        await pre_checkout.answer(ok=True)
    except Exception as e:
        logger.exception('Error in pre_checkout fallback: %s', e)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message):
    """Обработка успешной оплаты."""
    payment = message.successful_payment
    logger.info(
        'Successful payment received: user=%s, charge=%s, amount=%s',
        message.from_user.id,
        payment.telegram_payment_charge_id,
        payment.total_amount,
    )
    try:
        await _payment.process_successful_payment(
            user_id=message.from_user.id,
            charge_id=payment.telegram_payment_charge_id,
            total_amount=payment.total_amount,
        )
        # Получаем ссылку на канал
        invite_link = await _sub_service.get_invite_link()

        if invite_link:
            await message.answer(
                '✅ <b>Оплата прошла успешно!</b>\n\n'
                'Теперь у вас есть доступ к каналу.\n'
                'Нажмите кнопку ниже, чтобы вступить:',
                reply_markup=one_time_channel_invite_kb(invite_link),
            )
        else:
            await message.answer(
                '✅ Оплата прошла успешно!\n\n'
                'Теперь у вас есть доступ к каналу.\n'
                'Скоро вы получите приглашение.'
            )
    except Exception as e:
        logger.exception('Ошибка при обработке оплаты: %s', e)
        await message.answer(
            'Оплата получена, но произошла ошибка при активации.\n'
            'Обратитесь к администратору с ID платежа: '
            f'<code>{payment.telegram_payment_charge_id}</code>'
        )
