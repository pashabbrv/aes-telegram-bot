from dotenv import load_dotenv
import os
from telebot import TeleBot, types
from telebot.util import content_type_media

from .bot_main_menu import main_menu
from .bot_states import MainMenuState, FeedbackState
from ..text_information import CANCEL


load_dotenv()
manager = int(os.getenv('MANAGER_FEEDBACK'))


def register_commands(bot: TeleBot):
    '''Регистрация последовательности действий для оставления отзыва о боте'''

    # Обработчки, вызываемый при нажатии "Оставить отзыв о боте"
    @bot.message_handler(
        state=MainMenuState.main,
        func=lambda msg: msg.text == 'Оставить отзыв о боте',
    )
    def main_handler(message):
        bot.set_state(message.from_user.id, FeedbackState.main, message.chat.id)
        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        ).add(CANCEL)
        bot.send_message(
            chat_id=message.chat.id,
            text='Введи текст отзыва.',
            reply_markup=keyboard
        )
    

    # Ввод отзыва
    @bot.message_handler(
        state=FeedbackState.main,
        content_types=['text']
    )
    def feedback_handler(message):
        if manager == 0 and message.text != CANCEL:
            bot.send_message(
                chat_id=message.chat.id,
                text='Отзыв отправить не удалось. Менеджер по отзывам не назначен.'
            )
        elif message.text != CANCEL:
            try:
                bot.send_message(
                    chat_id=manager,
                    text=f'Пользователь оставил отзыв:\n\n{message.text}'
                )
                bot.send_message(
                    chat_id=message.chat.id,
                    text='Отзыв успешно отправлен.'
                )
            except Exception:
                bot.send_message(
                    chat_id=message.chat.id,
                    text='Отзыв отправить не удалось.'
                )
        main_menu(bot, message)
    

    @bot.message_handler(
        state=FeedbackState.main,
        content_types=content_type_media
    )
    def another_types_handler(message):
        bot.send_message(
            chat_id=message.chat.id,
            text='Пожалуйста, пиши только текст.'
        )
