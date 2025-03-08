
from dotenv import load_dotenv
from os import getenv
from pathlib import Path
import requests
import shelve
from telebot import TeleBot, types

import text_information as text_info

# Load consts from .env
load_dotenv()
bot_token = getenv('TG_BOT_TOKEN')

bot = TeleBot(token=bot_token)

# Connect to local storage
storage = shelve.open('education')

@bot.message_handler(commands=['start'])
def greeting(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Приветствуем тебя в ПИШ!')
    start(message)


def start(message):
    chat_id = message.chat.id
    # Create reply keyboard
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*['Узнать подробнее о ПИШ', 'Выбрать уровень образования'], row_width=2)
    # Send message with keyboard
    bot.send_message(
        chat_id=chat_id,
        text='Выбирай интересующие тебя темы, чтобы узнать о \"Передовой инженерной школе\" подробнее.',
        reply_markup=keyboard
    )
    bot.register_next_step_handler(message, first_choice)


def first_choice(message):
    chat_id = message.chat.id
    text = message.text
    if text == 'Узнать подробнее о ПИШ':
        bot.send_message(chat_id, 'Здесь содержится развёрнутая информация о ПИШ.')
        bot.register_next_step_handler(message, first_choice)
    elif text == 'Выбрать уровень образования':
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(*text_info.education.keys(), text_info.to_start, row_width=2)
        bot.send_message(
            chat_id=chat_id,
            text='Выбери уровень образования, на котором ты собираешься обучаться.',
            reply_markup=keyboard
        )
        bot.register_next_step_handler(message, education_choice)
    else:
        unknown_message(message, first_choice)


def education_choice(message):
    chat_id = message.chat.id
    text = message.text
    if text not in ['Бакалавриат', 'Магистратура']:
        unknown_message(message, education_choice)
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        # Make replies from specialization list
        keyboard.add(*text_info.education[text], text_info.to_start, row_width=1)
        bot.send_message(
            chat_id=chat_id,
            text='Выбери специальность, о которой хочешь узнать больше.',
            reply_markup=keyboard
        )
        bot.register_next_step_handler(message, info)


def info(message):
    chat_id = message.chat.id
    text = message.text
    if text not in text_info.education['Бакалавриат'] + text_info.education['Магистратура']:
        unknown_message(message, info)
    else:
        # Save specialization to local storage
        storage[str(chat_id)] = text
        show_questions(message)


def show_questions(message):
    chat_id = message.chat.id
    # Make replies from question list
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*text_info.questions, 'НЕТ НУЖНОГО ОТВЕТА', text_info.to_start, row_width=1)
    bot.send_message(
        chat_id=chat_id,
        text='Выбери, что тебя интересует.',
        reply_markup=keyboard
    )
    bot.register_next_step_handler(message, answer_question)


def answer_question(message):
    chat_id = message.chat.id
    text = message.text
    if text == 'НЕТ НУЖНОГО ОТВЕТА':
        # Make replies from question recipients list
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(*text_info.question_recipient, text_info.back, row_width=1)
        bot.send_message(
            chat_id=chat_id,
            text='Выбери, кому ты хочешь задать вопрос.',
            reply_markup=keyboard
        )
        bot.register_next_step_handler(message, recipient)
    elif text not in text_info.questions:
        unknown_message(message, answer_question)
    else:
        # Read specialization from local storage
        specialization = storage[str(chat_id)]
        # Answer the question
        bot.send_message(
            chat_id=chat_id, 
            text=f'Ответ на вопрос \"{text}\" по специальности {specialization}.'
        )
        bot.register_next_step_handler(message, answer_question)


def recipient(message):
    chat_id = message.chat.id
    text = message.text
    if text == text_info.back:
        show_questions(message)
    elif text not in text_info.question_recipient:
        unknown_message(message, recipient)
    else:
        # Add recipient to local storage
        storage[str(chat_id) + '_mail'] = [text]
        # Remove reply keyboard
        remove_keyboard = types.ReplyKeyboardRemove()
        bot.send_message(
            chat_id=chat_id, 
            text=f'Укажи свою фамилию и имя.',
            reply_markup=remove_keyboard
        )
        bot.register_next_step_handler(message, first_last_name)


def first_last_name(message):
    chat_id = message.chat.id
    text = message.text
    # Add first name and last name to local storage
    mail_info = storage[str(chat_id) + '_mail']
    mail_info.append(text)
    storage[str(chat_id) + '_mail'] = mail_info
    bot.send_message(chat_id, 'Укажи свой адрес электронной почты, на который будет отправлен ответ.')
    bot.register_next_step_handler(message, email)


def email(message):
    chat_id = message.chat.id
    text = message.text
    # Add email to local storage
    mail_info = storage[str(chat_id) + '_mail']
    mail_info.append(text)
    storage[str(chat_id) + '_mail'] = mail_info
    bot.send_message(chat_id, 'Напиши свой вопрос.')
    bot.register_next_step_handler(message, open_question)


def open_question(message):
    chat_id = message.chat.id
    text = message.text
    # Get info from local storage
    mail_info = storage[str(chat_id) + '_mail']
    # Send mail
    bot.send_message(
        chat_id, 
        f'to: {mail_info[0]}\nfrom: {mail_info[1]}\nemail: {mail_info[2]}\ntext:\n{text}'
    )
    del storage[str(chat_id) + '_mail']
    bot.send_message(chat_id, 'Твой вопрос успешно отправлен.\n'
                    'Ответ скоро придет тебе на указанный адрес электронной почты.')
    bot.send_message(chat_id, 'ЖДЕМ ТЕБЯ В ПИШ!')
    start(message)


def unknown_message(message, next_step):
    if message.text == text_info.to_start:
        start(message)
    else:
        chat_id = message.chat.id
        bot.send_message(chat_id, 'Я не знаю, что на это ответить. ' 
                        'Выбери, пожалуйста, один вариант из предложенных.')
        bot.register_next_step_handler(message, next_step)


if __name__ == '__main__':
    bot.polling()

# Close connection with local storage
storage.close()
