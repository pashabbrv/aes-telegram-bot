from telebot import TeleBot, types
from telebot.util import content_type_media

from .bot_main_menu import main_menu
from .bot_states import MainMenuState, AnswerState
from ..managers import managers
from ..text_information import CANCEL


def register_commands(bot: TeleBot):
    '''Ответ пользователю на вопрос от менеджера'''

    # Обработчки, вызываемый при нажатии "Ответить на вопрос"
    @bot.message_handler(
        state=MainMenuState.main,
        func=lambda msg: msg.text == 'Ответить на вопрос' and msg.from_user.id in managers.values(),
    )
    def main_handler(message):
        ask_id(message)
    

    # Выбор id пользователя, которому предоставить ответ
    def ask_id(message):
        bot.set_state(message.from_user.id, AnswerState.enter_id, message.chat.id)
        
        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        ).add(CANCEL)
        bot.send_message(
            chat_id=message.chat.id,
            text='Введите id пользователя, которому хотите ответить.',
            reply_markup=keyboard
        )
    

    @bot.message_handler(
        state=AnswerState.enter_id,
        func=lambda msg: msg.text != CANCEL
    )
    def ask_id_handler(message):
        text = message.text
        try:
            text = int(text)
        except Exception:
            bot.send_message(
                chat_id=message.chat.id,
                text='Некорректный ввод.'
            )
            return
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['answer_id'] = text
        bot.set_state(message.from_user.id, AnswerState.enter_answer, message.chat.id)
        bot.send_message(
            chat_id=message.chat.id,
            text='Введите ответ пользователю.'
        )
    

    @bot.message_handler(
        state=AnswerState.enter_answer,
        content_types=['text'],
        func=lambda msg: msg.text != CANCEL
    )
    def answer_handler(message):
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            chat_id = data['answer_id']
        try:
            # Ответ пользователю
            bot.send_message(
                chat_id=chat_id,
                text=f'Ответ от менеджера:\n\n{message.text}'
            )
            bot.send_message(
                chat_id=message.chat.id,
                text='Ответ пользователю успешно отправлен.'
            )
        except Exception:
            bot.send_message(
                chat_id=message.chat.id,
                text='Не удалось отправить ответ пользователю.'
            )
        main_menu(bot, message)
        
    
    # Отмена ввода и возврат в главное меню
    @bot.message_handler(
        state=[AnswerState.enter_id, AnswerState.enter_answer],
        func=lambda msg: msg.text == CANCEL
    )
    def cancel_handler(message):
        main_menu(bot, message)
    

    # Просьба отправлять только текстовые сообщения
    @bot.message_handler(
        state=[AnswerState.enter_id, AnswerState.enter_answer],
        content_types=content_type_media
    )
    def other_messages_handler(message):
        bot.send_message(
            chat_id=message.chat.id, 
            text=f'Пожалуйста, пишите только текст.'
        )
