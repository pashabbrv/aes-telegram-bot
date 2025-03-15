from dotenv import load_dotenv
import os
from telebot import TeleBot, types, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.util import content_type_media

from .bot_handlers.bot_states import *
from .bot_handlers.main_menu import main_menu
from .bot_handlers import bot_specialization
from .text_information import *
#import email_handler

# Загрузка констант из .env
load_dotenv()
bot_token = os.getenv('TG_BOT_TOKEN')

# Создание бота и хранилища
state_storage = StateMemoryStorage()
bot = TeleBot(token=bot_token, state_storage=state_storage)
bot.add_custom_filter(custom_filters.StateFilter(bot))


# Обработка команды /start
@bot.message_handler(commands=['start'])
def start_command_handler(message):
    bot.set_state(message.from_user.id, StartState.start, message.chat.id)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add('Начать')
    bot.send_message(
        chat_id=message.chat.id, 
        text='Привет! Я – твой помощник для поступления в Передовую '
        'инженерную школу ЛЭТИ. Готов помочь тебе разобраться в '
        'программах обучения, рассказать о возможностях поступления '
        'и ответить на вопросы. Добро пожаловать!',
        reply_markup=keyboard
    )


@bot.message_handler(
    state=StartState.start,
    func=lambda msg: msg.text == 'Начать',
)
def start_handler(message):
    bot.set_state(message.from_user.id, MainMenuState.main, message.chat.id)
    photo_url = 'https://pish.etu.ru/assets/cache/images/bessonov-400x400-1f7.jpg'
    bot.send_photo(
        chat_id=message.chat.id,
        photo=photo_url,
        caption='\"Хочешь стать инженером нового поколения, лучше и '
        'перспективнее других? Выбирай Передовую инженерную школу ЛЭТИ!\"'
    )
    go_to_main_menu(message)


@bot.message_handler(
    state=MainMenuState.main,
    func=lambda msg: msg.text == 'Узнать подробнее о ПИШ',
)
def start_handler(message):
    bot.send_message(
        chat_id=message.chat.id,
        text='- [Кратко о том, чем ПИШ отличается от классических образовательных программ.]\n'
        '- Возможности участия в реальных промышленных проектах.\n'
        '- Партнёрства с компаниями, современные лаборатории, перспектива трудоустройства.\n'
    )
    main_menu(bot, message)


bot_specialization.register_commands(bot)


@bot.message_handler(
    func=lambda msg: msg.text in START
)
def go_to_main_menu(message):
    main_menu(bot, message)


@bot.message_handler(
    content_types=content_type_media
)
def unknown_message_handler(message):
    bot.send_message(
        chat_id=message.chat.id,
        text='Выбери один вариант из предложенных'
    )


if __name__ == '__main__':
    bot.polling()
