from aiogram.fsm.state import State, StatesGroup


class SosStates(StatesGroup):
    confirmation = State()
    submit = State()


class PaymentStates(StatesGroup):
    """Состояния для процесса оплаты через YooMoney."""
    waiting_payment = State()  # Ожидание оплаты — пользователь перешёл по ссылке


class SubscriptionStates(StatesGroup):
    """Состояния для проверки подписки на канал."""
    waiting_subscription = State()  # Ожидание подписки — пользователь должен вернуться в канал

