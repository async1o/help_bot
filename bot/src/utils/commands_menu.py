from aiogram.types import BotCommand

from typing import List

def get_keyboard_for_menu() -> List[BotCommand]:
    commands = {
        '/start': 'Начинает диалог с ботом',
        '/check_subscription': 'Проверить подписку на канал',
    }

    keyboard = [BotCommand(command=command, description=desc) for command, desc in commands.items()]
    

    return keyboard
