"""Обработчики callbacks для оплаты через YooMoney."""

import logging

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from src.services.yoomoney_service import YooMoneyService
from src.db.repositories import UserRepository
from src.keyboards.payment import yoomoney_pay_kb, restore_start_kb, restore_invite_kb, one_time_channel_invite_kb
from src.states.sos_states import PaymentStates
from src.utils.config import settings
from src.utils.pay import YooMoneyProcessor
from src.services.subscription_service import SubscriptionService

router = Router()
_yoomoney = YooMoneyService()

logger = logging.getLogger(__name__)


@router.callback_query(F.data == 'pay_yoomoney')
async def show_yoomoney_payment(callback: CallbackQuery, state: FSMContext):
    """Показать описание услуги и ссылку на оплату через YooMoney."""
    user_id = callback.from_user.id

    # Проверяем, не оплатил ли уже
    user = await UserRepository().get_user_by_id(str(user_id))
    if user and user.is_paid:
        await callback.answer('У вас уже есть доступ!', show_alert=True)
        return

    try:
        payment_url = await _yoomoney.generate_payment_link(user_id)

        price_text = f'{settings.PAYMENT_PRICE_RUB}₽'

        text = (
            f'💳 <b>Доступ к закрытому каналу через YooMoney</b>\n\n'
            f'Одноразовая оплата за <b>бессрочный</b> доступ.\n\n'
            f'✅ Полный доступ ко всем материалам\n'
            f'✅ Без ежемесячных платежей\n\n'
            f'💰 Стоимость: <b>{price_text}</b>\n\n'
            f'Нажмите кнопку ниже, перейдите на страницу оплаты и оплатите. '
            f'После оплаты нажмите «Я оплатил» для проверки.'
        )

        await callback.message.edit_text(text, reply_markup=yoomoney_pay_kb(payment_url))

        await state.set_state(PaymentStates.waiting_payment)
        await callback.answer()
    except Exception as e:
        logger.exception('Ошибка при создании YooMoney ссылки: %s', e)
        await callback.answer('Не удалось создать ссылку для оплаты. Попробуйте позже.', show_alert=True)


@router.callback_query(F.data == 'yoomoney_check', PaymentStates.waiting_payment)
async def check_yoomoney_payment(callback: CallbackQuery, state: FSMContext):
    """Проверить оплату YooMoney и активировать подписку."""
    user_id = callback.from_user.id
    user_id_str = str(user_id)
    logger.info('YooMoney payment check requested: user=%s', user_id)

    await callback.answer('Проверяю оплату...')

    try:
        # Ищем успешную оплату по метке user_{user_id}_
        async with YooMoneyProcessor() as processor:
            history = await processor.get_operation_history()

            found_op = None
            for op in history.operations:
                if (op.status == 'success'
                        and op.label
                        and f'user_{user_id}_' in op.label):
                    found_op = op
                    break

            # Если не нашли в истории — пробуем прямой поиск по сумме
            if found_op is None:
                for op in history.operations:
                    if op.status == 'success' and op.amount == settings.PAYMENT_PRICE_RUB:
                        found_op = op
                        break

        if found_op:
            # Активируем подписку напрямую — оплата уже подтверждена из API
            from src.db.repositories import PaymentRepository
            from src.schemas.payments import PaymentSchema

            label = found_op.label
            charge_id = f"yoomoney_{label}"

            logger.info('Activating subscription for user=%s, label=%s', user_id, label)

            # Записываем платёж (с защитой от дублей)
            await PaymentRepository().add_payment(PaymentSchema(
                user_id=user_id_str,
                telegram_payment_charge_id=charge_id,
                amount=found_op.amount,
                currency='RUB',
            ))

            # Активируем подписку
            await PaymentRepository().activate_user_subscription(user_id_str)

            # Получаем ссылку на канал
            invite_link = await _subscription_service.get_invite_link()

            if invite_link:
                await callback.message.edit_text(
                    '✅ <b>Оплата прошла успешно!</b>\n\n'
                    'Теперь у вас есть доступ к каналу.\n'
                    'Нажмите кнопку ниже, чтобы вступить:',
                    reply_markup=one_time_channel_invite_kb(invite_link),
                )
            else:
                await callback.message.edit_text(
                    '✅ <b>Оплата прошла успешно!</b>\n\n'
                    'Теперь у вас есть доступ к каналу.\n'
                    'Скоро вы получите приглашение.'
                )
            await state.clear()
            logger.info('YooMoney payment processed and subscription activated: user=%s', user_id)
        else:
            logger.info('No matching payment found for user=%s', user_id)
            await callback.answer(
                'Оплата ещё не поступила. Если вы уже оплатили, подождите пару минут и попробуйте снова.\n\n'
                f'В истории {len(history.operations)} операций.',
                show_alert=True
            )

    except Exception as e:
        logger.exception('Ошибка при проверке YooMoney оплаты: %s', e)
        await callback.answer(
            f'Не удалось проверить оплату. Попробуйте позже или обратитесь к администратору.\n\n'
            f'Ошибка: {type(e).__name__}: {e}',
            show_alert=True,
        )


@router.message(PaymentStates.waiting_payment)
async def waiting_payment_message(message):
    """Обрабатывать сообщения в состоянии ожидания оплаты."""
    await message.answer(
        '💳 Пожалуйста, перейдите по ссылке на оплату в меню выше. '
        'После оплаты нажмите кнопку «Я оплатил».'
    )


# ---- Проверка подписки и восстановление доступа ----

_subscription_service = SubscriptionService()


@router.callback_query(F.data == 'check_subscription_again')
async def check_subscription_again(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Проверить, вернулся ли пользователь в канал (обратная совместимость)."""
    user_id = callback.from_user.id

    is_subscribed = await _subscription_service.check_user_subscription(bot, user_id)

    if is_subscribed:
        # Восстанавливаем доступ если нужно
        await _subscription_service.on_user_returned(bot, user_id)
        # Создаём одноразовую ссылку на канал
        invite_link = await _subscription_service.get_invite_link()

        if invite_link:
            await callback.message.answer(
                '✅ <b>Добро пожаловать обратно!</b>\n\n'
                'Ваш доступ к боту восстановлен.\n\n'
                'Нажмите кнопку ниже, чтобы перейти в канал:',
                reply_markup=one_time_channel_invite_kb(invite_link),
            )
        else:
            await callback.message.answer(
                '✅ <b>Добро пожаловать обратно!</b>\n\n'
                'Ваш доступ к боту восстановлен.'
            )
        await state.clear()
        await callback.answer()
    else:
        await callback.message.edit_text(
            '⚠️ <b>Восстановление доступа</b>\n\n'
            'Вы всё ещё не подали заявку. '
            'Нажмите «Подать заявку» и дождитесь одобрения.',
            reply_markup=restore_start_kb(),
        )
        await callback.answer()


@router.callback_query(F.data == 'applied_to_channel')
async def restore_access(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Показать ссылку для подачи заявки в канал."""
    invite_link = await _subscription_service.get_invite_link()

    if invite_link is None:
        await callback.answer('Ссылка на канал не настроена, обратитесь к администратору.', show_alert=True)
        return

    await callback.message.edit_text(
        '📢 <b>Восстановление доступа</b>\n\n'
        'Нажмите «Подать заявку», чтобы перейти в канал. '
        'Бот автоматически одобрит вашу заявку и восстановит доступ.',
        reply_markup=restore_invite_kb(invite_link),
    )

    await callback.answer()


