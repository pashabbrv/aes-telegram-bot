from telebot import TeleBot
import redis
import os

from .bot_states import MainMenuState
from ..managers import management

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
        func=lambda msg: msg.text == 'Статистика' and msg.from_user.id in management,
    )
    def main_handler(message):
        management_count = 0
        for value in management:
            if value != 0:
                management_count += 1
        all_users_count = redis_storage.dbsize()
        bot.send_message(
            chat_id=message.chat.id,
            text=f'- Дирекция, имеющая доступ к статистике: {management_count}\n'
            f'- Количество пользователей (без дирекции): {max(0, all_users_count - management_count)}\n'
        )
    