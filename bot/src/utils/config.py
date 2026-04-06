from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    TOKEN: str
    ADMINS: str
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_NAME: str
    DB_PASS: str
    YOOMONEY_TOKEN: str

    # Оплата Telegram Payments
    PAYMENT_TOKEN: str = ''  # Получить: @BotFather → Your Bot → Payments → Connect

    # ID канала (для проверки подписки)
    # Формат: @channel_username или -100xxxxxxxxxx
    CHANNEL_ID: str = ''

    # Ссылка на канал для вступления/подачи заявки
    # Формат: https://t.me/+xxxxxxxxxx (постоянная ссылка-приглашение)
    CHANNEL_INVITE_LINK: str = ''

    # Прокси для обхода блокировок Telegram
    PROXY_URL: Optional[str] = None  # например: socks5://user:pass@1.2.3.4:1080
    PAYMENT_PRICE_RUB: int  # Цена доступа в рублях

    @property
    def get_url_db(self):
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    @property
    def is_proxy_enabled(self) -> bool:
        return self.PROXY_URL is not None and self.PROXY_URL != ''

    @property
    def is_payment_enabled(self) -> bool:
        return self.PAYMENT_TOKEN != ''

    @property
    def is_yoomoney_enabled(self) -> bool:
        return self.YOOMONEY_TOKEN is not None and self.YOOMONEY_TOKEN != ''

    @property
    def is_channel_set(self) -> bool:
        return self.CHANNEL_ID is not None and self.CHANNEL_ID != ''


    model_config = SettingsConfigDict(env_file='.env')

settings = Settings() #type: ignore
