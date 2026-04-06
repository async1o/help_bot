import logging

from aiogram import Router, F, Bot, types
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from src.db.repositories import UserRepository
from src.schemas.users import UserSchema
from src.states.sos_states import SosStates
from src.keyboards.sos import confirmation_kb, cancel_message, all_right_message
from src.keyboards.payment import main_menu_kb, restore_start_kb, restore_invite_kb, one_time_channel_invite_kb
from src.services.dialog_service import DialogService
from src.services.support_service import SupportService
from src.services.subscription_service import SubscriptionService
from src.filters.in_dialog import IsUserInDialog
from src.utils.config import settings

router = Router()
logger = logging.getLogger('UsersHandlers')
_support = SupportService()


@router.message(IsUserInDialog())
async def forward_user_message_to_operator(message: Message):
    """Пересылает сообщение пользователя оператору, когда идёт диалог."""
    sender_id = str(message.from_user.id)
    operator_id = await DialogService.get_operator_for_user(sender_id)
    if not operator_id:
        return
    try:
        await message.bot.copy_message(
            chat_id=operator_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
    except Exception as e:
        logger.exception('Не удалось переслать сообщение пользователя оператору: %s', e)


@router.message(F.text == '/start')
async def start(message: Message, bot: Bot, state: FSMContext):
    user_id = str(message.from_user.id)
    existing_user = await UserRepository().get_user_by_id(user_id)

    # Формируем имя — fallback на username или first_name
    display_name = message.from_user.full_name or message.from_user.username or f"пользователь {user_id}"

    if existing_user is None:
        # Новый пользователь — регистрируем
        user_schema = UserSchema(
            user_id=user_id,
            full_name=message.from_user.full_name or message.from_user.username,
            is_operator=False,
            is_admin=False
        )
        await UserRepository().add_user(user_schema)
        greeting = f'Здравствуйте, {display_name}!'
        await message.answer(
            text=f'{greeting}\nВыберите действие:',
            reply_markup=main_menu_kb(is_paid=False)
        )
    else:
        # Уже зарегистрирован — проверяем подписку на канал
        display_name = message.from_user.full_name or message.from_user.username or existing_user.full_name or f"пользователь {user_id}"

        if settings.is_channel_set and existing_user.has_paid_ever:
            is_subscribed = await _sub_service.check_user_subscription(bot, message.from_user.id)

            if not is_subscribed:
                # Пользователь выходил из канала — предлагаем восстановить доступ
                await message.answer(
                    text=f'⚠️ {display_name}, вы вышли из канала.\n\n'
                         'Для восстановления доступа нажмите «Восстановить доступ».',
                    reply_markup=restore_start_kb(),
                )
                return

            # Пользователь в канале — восстанавливаем доступ если нужно
            if not existing_user.is_paid:
                await _sub_service.on_user_returned(bot, message.from_user.id)

        try:
            await message.answer(
                text=f'С возвращением, {display_name}!\nВыберите действие:',
                reply_markup=main_menu_kb(is_paid=existing_user.is_paid)
            )
        except Exception as e:
            logger.error('Ошибка отправки сообщения пользователю %s: %s', user_id, e)

@router.message(F.text == '/sos')
async def start_sos(message: Message, state: FSMContext):
    await message.answer(text='Подробно опишите вашу проблему')
    await state.set_state(SosStates.confirmation)


@router.message(F.text == '/id')
async def get_id(message: Message):
    await message.answer(text=str(message.from_user.id))

@router.message(SosStates.confirmation)
async def confirm_request(message: Message, state: FSMContext):
    await state.update_data(submit=message.text)

    await message.answer(text='Убедитесь, что всё правильно', reply_markup=confirmation_kb())

    await state.set_state(SosStates.submit)

@router.message(lambda message: message.text not in [cancel_message, all_right_message], SosStates.submit)
async def incorrect_answer(message: Message):
    await message.answer(text='Такого варианта не было')

@router.message(F.text == cancel_message, SosStates.submit)
async def cancel_answer(message: Message, state: FSMContext):

    await message.answer(text='Отменено!', reply_markup=ReplyKeyboardRemove())

    await state.clear()

@router.message(F.text == all_right_message, SosStates.submit)
async def apply_answer(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        request_id = await _support.notify_operators(
            message.bot, data.get('submit', ''), message.from_user.id
        )
        if request_id:
            await message.answer(text='Запрос отправлен!', reply_markup=ReplyKeyboardRemove())
        else:
            await message.answer(
                text='К сожалению, сейчас нет доступных операторов. Попробуйте позже.',
                reply_markup=ReplyKeyboardRemove()
            )
    except Exception as e:
        logger.exception('apply_answer: %s', e)
        await message.answer(text='Что-то пошло не так', reply_markup=ReplyKeyboardRemove())
    finally:
        await state.clear()


# ---- Проверка подписки ----

_sub_service = SubscriptionService()

SUBSCRIPTION_REQUIRED_TEXT = (
    '⚠️ <b>Доступ ограничен</b>\n\n'
    'Вы вышли из канала. Для восстановления доступа '
    '<b>перейдите в канал и подайте заявку на вступление</b>, '
    'затем нажмите кнопку ниже.\n\n'
    'После одобрения вам снова будет доступен весь функционал бота.'
)

SUBSCRIBED_TEXT = (
    '✅ <b>Добро пожаловать обратно!</b>\n\n'
    'Ваш доступ к боту восстановлен.'
)


@router.message(F.text == '/check_subscription')
async def check_subscription_command(message: Message, bot: Bot, state: FSMContext):
    """Команда для проверки/восстановления подписки на канал."""
    if not settings.is_channel_set:
        await message.answer('Проверка подписки не настроена (CHANNEL_ID не указан).')
        return

    user_id = message.from_user.id
    is_subscribed = await _sub_service.check_user_subscription(bot, user_id)

    if is_subscribed:
        await _sub_service.on_user_returned(bot, user_id)
        invite_link = await _sub_service.get_invite_link()

        if invite_link:
            await message.answer(
                SUBSCRIBED_TEXT + '\n\nНажмите кнопку ниже, чтобы перейти в канал:',
                reply_markup=one_time_channel_invite_kb(invite_link),
            )
        else:
            await message.answer(SUBSCRIBED_TEXT, reply_markup=main_menu_kb(is_paid=True))
        await state.clear()
    else:
        await message.answer(
            SUBSCRIPTION_REQUIRED_TEXT,
            reply_markup=restore_start_kb(),
        )


# ---- Обработка заявок на вступление в канал ----

@router.chat_join_request()
async def on_join_request(join_request: types.ChatJoinRequest, bot: Bot):
    """Обработка заявки на вступление — одобрить только если оплачен доступ."""
    from src.db.repositories import PaymentRepository

    user_id = str(join_request.from_user.id)
    logger.info('Заявка на вступление от user=%s', user_id)

    # Проверяем, оплачивал ли пользователь доступ
    user = await UserRepository().get_user_by_id(user_id)

    if user is None or not user.has_paid_ever:
        # Не оплатил — отклоняем заявку
        logger.info('Заявка отклонена: user=%s не оплатил доступ', user_id)
        await join_request.decline()

        # Если новый пользователь — регистрируем
        if user is None:
            user_schema = UserSchema(
                user_id=user_id,
                full_name=join_request.from_user.full_name,
                is_operator=False,
                is_admin=False,
            )
            await UserRepository().add_user(user_schema)

        try:
            await bot.send_message(
                chat_id=join_request.from_user.id,
                text='❌ <b>Заявка отклонена</b>\n\n'
                     'Для получения доступа оплатите подписку через бота.',
                reply_markup=main_menu_kb(is_paid=False),
                parse_mode='HTML',
            )
        except Exception as e:
            logger.error('Не удалось отправить сообщение user=%s: %s', user_id, e)
        return

    # Оплатил — одобряем и восстанавливаем доступ
    await join_request.approve()
    await PaymentRepository().activate_user_subscription(user_id)
    logger.info('Заявка одобрена и доступ восстановлен для user=%s', user_id)

    try:
        invite_link = await _sub_service.get_invite_link()
        if invite_link:
            await bot.send_message(
                chat_id=join_request.from_user.id,
                text='✅ <b>Ваша заявка одобрена!</b>\n\n'
                     'Доступ к боту восстановлен.\n'
                     'Нажмите кнопку ниже, чтобы перейти в канал:',
                reply_markup=one_time_channel_invite_kb(invite_link),
                parse_mode='HTML',
            )
        else:
            await bot.send_message(
                chat_id=join_request.from_user.id,
                text='✅ <b>Ваша заявка одобрена!</b>\n\n'
                     'Доступ к боту восстановлен.',
                parse_mode='HTML',
            )
    except Exception as e:
        logger.error('Не удалось отправить сообщение user=%s: %s', user_id, e)



