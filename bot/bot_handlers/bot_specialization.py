from telebot import TeleBot, types

from .bot_main_menu import main_menu
from .bot_states import MainMenuState, SpecializationState
from ..text_information import *

def register_commands(bot: TeleBot):
    '''Регистрация последовательности действий для специальностей'''

    # Обработчки, вызываемый при нажатии "Выбрать уровень образования"
    @bot.message_handler(
        state=MainMenuState.main,
        func=lambda msg: msg.text == 'Выбрать уровень образования',
    )
    def main_handler(message):
        specialization_choice(message)
    

    # Выбор уровня образования
    def specialization_choice(message):
        bot.set_state(message.from_user.id, SpecializationState.main_choice, message.chat.id)
        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        ).add(*EDUCATION.keys(), BACK, START, row_width=2)
        bot.send_message(
            chat_id=message.chat.id,
            text='Выбери уровень образования, на котором ты собираешься обучаться.',
            reply_markup=keyboard
        )
    

    @bot.message_handler(
        state=SpecializationState.main_choice,
        func=lambda msg: msg.text in EDUCATION.keys() or msg.text == BACK
    )
    def specialization_handler(message):
        if message.text == BACK:
            main_menu(bot, message)
        else:
            specialization(message)
    

    # Выбор специальности
    def specialization(message):
        bot.set_state(message.from_user.id, SpecializationState.specialization, message.chat.id)
        # Сохранение уровня образования
        text = message.text
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            if text != BACK:
                data['education_level'] = text
            else:
                text = data['education_level']
        # Создание ответа пользователю
        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        ).add(
            *EDUCATION[text], row_width=1
        ).add(BACK, START, row_width=2)
        bot.send_message(
            chat_id=message.chat.id,
            text='Выбери специальность, о которой хочешь узнать больше.',
            reply_markup=keyboard
        )
    

    def specialization_or_back_checker(message):
        if bot.get_state(message.from_user.id, message.chat.id) == SpecializationState.specialization.name:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                specialization_level = data['education_level']
            return message.text in (EDUCATION[specialization_level] + [BACK])
        return False


    @bot.message_handler(
        state=SpecializationState.specialization,
        func=specialization_or_back_checker,
    )
    def specialization_handler(message):
        if message.text == BACK:
            specialization_choice(message)
        else:
            questions(message)
    

    # Выбор вопроса
    def questions(message):
        bot.set_state(message.from_user.id, SpecializationState.question, message.chat.id)
        # Сохранение уровня образования
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['education'] = message.text
            education_level = data['education_level']
        # Создание ответа пользователю
        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        ).add(
            *QUESTIONS, BACK, START,
            row_width=2
        )
        bot.send_message(
            chat_id=message.chat.id,
            text='Выбери, что тебя интересует.',
            reply_markup=keyboard
        )


    @bot.message_handler(
        state=SpecializationState.question,
        func=lambda msg: msg.text in QUESTIONS + [BACK],
    )
    def question_handler(message):
        if message.text == BACK:
            specialization(message)
        else:
            answer_question(message)
    

    # Ответ на вопрос
    def answer_question(message):
        chat_id = message.chat.id
        text = message.text

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            education_level = data['education_level']
            specialization = data['education']
        
        bot.send_message(
            chat_id=chat_id, 
            text=f'Ответ на вопрос \"{text}\" по специальности \"{education_level}. {specialization}\".'
        )
