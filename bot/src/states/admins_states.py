from aiogram.fsm.state import State, StatesGroup


class AddStates(StatesGroup):
    admins = State()
    operator = State()


class DeleteStates(StatesGroup):
    admins = State()
    operator = State()
