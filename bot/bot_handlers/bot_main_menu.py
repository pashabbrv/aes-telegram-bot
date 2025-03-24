from telebot import types, TeleBot

from .bot_states import MainMenuState
from ..managers import managers


def main_menu(bot: TeleBot, message):
    bot.set_state(message.from_user.id, MainMenuState.main, message.chat.id)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
        'Узнать подробнее о ПИШ', 
        'Выбрать уровень образования',
        'Задать вопрос боту',
        'Оставить отзыв о боте',
        row_width=2
    )
    # Для менеджеров добавляем кнопку для ответа на вопрос
    if message.from_user.id in managers.values():
        keyboard.add('Ответить на вопрос', row_width=2)
    bot.send_message(
        chat_id=message.chat.id,
        text='Выбери интересующий тебя раздел.',
        reply_markup=keyboard
    )