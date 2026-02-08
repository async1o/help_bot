import logging

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from src.db.repositories import UserRepository
from src.schemas.users import UserSchema
from src.states.sos_states import SosStates
from src.keyboards.sos import confirmation_kb, cancel_message, all_right_message
from src.services.dialog_service import DialogService
from src.services.support_service import SupportService
from src.filters.in_dialog import IsUserInDialog

router = Router()
logger = logging.getLogger('UsersHandlers')
_support = SupportService()


@router.message(IsUserInDialog())
async def forward_user_message_to_operator(message: Message):
    """Пересылает сообщение пользователя оператору, когда идёт диалог."""
    operator_id = DialogService.get_operator_for_user(str(message.from_user.id))
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
async def start(message: Message):
    user_schema = UserSchema(user_id=str(message.from_user.id),
                             full_name=message.from_user.full_name,
                             is_operator=False,
                             is_admin=False)
    
    await UserRepository().add_user(user_schema)
    await message.answer(text=f'Здравствуйте {message.from_user.full_name}\nЕсли хотите задать вопрос напишите <b>/sos</b>')

@router.message(F.text == '/sos')
async def start_sos(message: Message, state: FSMContext):
    await message.answer(text='Подробно опишите вашу проблему')
    await state.set_state(SosStates.confirmation)


@router.message(F.text == '/id')
async def get_id(message: Message):
    await message.answer(text=str(message.from_user.id))

@router.message(SosStates.confirmation)
async def confirm_request(message: Message, state: FSMContext):
    await state.update_data(sumbit=message.text)

    await message.answer(text='Убедитесь, что всё правильно', reply_markup=confirmation_kb())

    await state.set_state(SosStates.sumbit)
    
@router.message(lambda message: message.text not in [cancel_message, all_right_message], SosStates.sumbit)
async def incorrect_answer(message: Message):
    await message.answer(text='Такого варианта не было')

@router.message(F.text == cancel_message, SosStates.sumbit)
async def cancel_answer(message: Message, state: FSMContext):

    await message.answer(text='Отменено!', reply_markup=ReplyKeyboardRemove())

    await state.clear()

@router.message(F.text == all_right_message, SosStates.sumbit)
async def apply_answer(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        request_id = await _support.notify_operators(
            message.bot, data.get('sumbit', ''), message.from_user.id
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



