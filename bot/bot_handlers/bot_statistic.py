from telebot import TeleBot
import redis
import os

from .bot_states import MainMenuState
from ..managers import managers

# Подключение к redis
redis_host = os.getenv('REDIS_HOST')
redis_port = int(os.getenv('REDIS_PORT'))
redis_storage = redis.Redis(
    host=redis_host, 
    port=redis_port
)


def register_commands(bot: TeleBot):
    '''Получение статистики бота менеджером'''

    # Обработчки, вызываемый при нажатии "Ответить на вопрос"
    @bot.message_handler(
        state=MainMenuState.main,
        func=lambda msg: msg.text == 'Статистика' and msg.from_user.id in managers.values(),
    )
    def main_handler(message):
        managers_count = 0
        for value in set(managers.values()):
            if value != 0:
                managers_count += 1
        all_users_count = redis_storage.dbsize()
        bot.send_message(
            chat_id=message.chat.id,
            text=f'- Количество назначенных менеджеров: {managers_count}\n'
            f'- Количество пользователей (без менеджеров): {max(0, all_users_count - managers_count)}\n'
        )
    