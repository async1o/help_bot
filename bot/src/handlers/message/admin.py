import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from src.filters.is_admin import IsAdmin
from src.db.repositories import AdminRepository
from src.states.admins_states import AddStates, DeleteStates

router = Router()
router.message.filter(IsAdmin())

logger = logging.getLogger("AdminsHandler")


class Admins:
    @router.message(F.text == "/admin")
    async def admin_panel(message: Message):
        text = (
            "<b>/add_admin</b> - Назначает нового администратора\n"
            "<b>/delete_admin</b> - Удаляет администратора\n"
            "<b>/add_operator</b> - Назначает нового оператора\n"
            "<b>/delete_operator</b> - Удаляет оператора"
        )

        await message.answer(text=text)

    @router.message(F.text == "/add_admin")
    async def add_admin(message: Message, state: FSMContext):
        await message.answer(text="Введите ID нового администратора")

        await state.set_state(AddStates.admins)

    @router.message(AddStates.admins)
    async def add_admin_2(message: Message, state: FSMContext):
        try:
            await AdminRepository().update_roles(
                user_id=str(message.text), add=True, operator=False
            )

            await message.answer(text="Администартор успешно добавлен")
        except NotImplementedError:
            await message.answer(
                text="Перед добавлением нового администратора, убедитесь что он использовал бота"
            )
        except Exception as e:
            await message.answer(text="Что-то пошло не так")

            logger.error(msg=e)

        finally:
            await state.clear()

    @router.message(F.text == "/delete_admin", IsAdmin())
    async def delete_admin(message: Message, state: FSMContext):
        await message.answer(text="Введите ID администратора")

        await state.set_state(DeleteStates.admins)

    @router.message(DeleteStates.admins)
    async def delete_admin_2(message: Message, state: FSMContext):
        try:
            await AdminRepository().update_roles(
                user_id=str(message.text), add=False, operator=False
            )

            await message.answer(text="Администратор успешно удален")
        except NotImplementedError:
            await message.answer(text="Такого администратора не существует")
        except Exception as e:
            await message.answer(text="Что-то пошло не так")

            logger.error(msg=e)

        finally:
            await state.clear()


class Operators:
    @router.message(F.text == "/add_operator", IsAdmin())
    async def add_operator(message: Message, state: FSMContext):
        await message.answer(text="Введите ID нового оператора")

        await state.set_state(AddStates.operator)

    @router.message(AddStates.operator)
    async def add_operator_2(message: Message, state: FSMContext):
        try:
            await AdminRepository().update_roles(
                user_id=str(message.text), add=True, operator=True
            )

            await message.answer(text="Оператор успешно добавлен")
        except NotImplementedError:
            await message.answer(
                text="Перед добавлением нового оператора, убедитесь что он использовал бота"
            )
        except Exception as e:
            await message.answer(text="Что-то пошло не так")

            logger.error(msg=e)

        finally:
            await state.clear()

    @router.message(F.text == "/delete_operator", IsAdmin())
    async def delete_operator(message: Message, state: FSMContext):
        await message.answer(text="Введите ID оператора")

        await state.set_state(DeleteStates.operator)

    @router.message(DeleteStates.operator)
    async def delete_operator_2(message: Message, state: FSMContext):
        try:
            await AdminRepository().update_roles(
                user_id=str(message.text), add=False, operator=True
            )

            await message.answer(text="Оператор успешно удален")
        except NotImplementedError:
            await message.answer(text="Такого оператора не существует")
        except Exception as e:
            await message.answer(text="Что-то пошло не так")

            logger.error(msg=e)

        finally:
            await state.clear()
