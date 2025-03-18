from telebot import TeleBot, types
from telebot.util import content_type_media
from time import sleep

from .bot_main_menu import main_menu
from .bot_states import MainMenuState, QuestionState
from ..text_information import START

def register_commands(bot: TeleBot):
    '''Ответ пользователю на вопрос от нейросети'''
    #from . import LLM_integration as LLM

    # Обработчки, вызываемый при нажатии "Задать вопрос боту"
    @bot.message_handler(
        state=MainMenuState.main,
        func=lambda msg: msg.text == 'Задать вопрос боту',
    )
    def main_handler(message):
        ask_question(message)
    

    # Вопрос нейросети от пользователя
    def ask_question(message):
        bot.set_state(message.from_user.id, QuestionState.ask_question, message.chat.id)
        # Получение количества оставшихся запросов пользователя
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            try:
                n = data['questions_n']
            except Exception as e:
                # Если пользователь ни разу не задавал вопрос, то даём ему количество запросов
                n = 5
                data['questions_n'] = n
        
        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        ).add(START, row_width=2)
        bot.send_message(
            chat_id=message.chat.id,
            text='Задай интересующий тебя вопрос и наша нейросеть даст на него ответ '
            '(во время ожидания ответа тебе нельзя будет перемещаться между разделами).'
            f'\nОставшееся количество запросов: {n}',
            reply_markup=keyboard
        )
    

    @bot.message_handler(
        state=QuestionState.ask_question
    )
    def ask_question_handler(message):
        chat_id = message.chat.id
        text = message.text

        if text == START:
            main_menu(bot, message)
            return
        
        # Открытие хранилища для проверки оставшегося количества запросов
        with bot.retrieve_data(message.from_user.id, chat_id) as data:
            n = data['questions_n']
            # Если количество запросов исчерпано, то выводим сообщение
            if n == 0:
                bot.send_message(
                    chat_id=chat_id, 
                    text=f'Прости, но твой лимит по вопросам исчерпан.'
                )
                return
            data['questions_n'] = n - 1
        
        # Состояние ожидания ответа
        bot.set_state(message.from_user.id, QuestionState.wait_answer, message.chat.id)
        # Генерирование ответа на вопрос
        '''response = LLM.LLM_chain(text)'''
        sleep(5)
        response = 'Ожидание 5 секунд'
        # Отправка ответа пользователю
        bot.send_message(
            chat_id=chat_id, 
            text=f'Ответ на вопрос \"{text}\":\n\n{response}'
        )
        # Возврат к этапу задавания вопроса
        ask_question(message)
    

    # Ожидание ответа на вопрос
    @bot.message_handler(
        state=QuestionState.wait_answer,
        content_types=content_type_media
    )
    def ask_question_handler(message):
        bot.send_message(
            chat_id=message.chat.id, 
            text=f'Пожалуйста, дождись, пока нейросеть сгенерирует ответ.'
        )
