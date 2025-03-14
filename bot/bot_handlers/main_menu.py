from telebot import types, TeleBot

from .bot_states import MainMenuState


def main_menu(bot: TeleBot, message):
    bot.set_state(message.from_user.id, MainMenuState.main, message.chat.id)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add('Выбрать уровень образования')
    bot.send_message(
        chat_id=message.chat.id,
        text='Выбери интересующий тебя раздел.',
        reply_markup=keyboard
    )