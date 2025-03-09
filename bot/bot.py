from dotenv import load_dotenv
from os import getenv
import shelve
from telebot import TeleBot

import text_information as text_info
import messages
import LLM_integration as LLM

# Загрузка констант из .env
load_dotenv()
bot_token = getenv('TG_BOT_TOKEN')

bot = TeleBot(token=bot_token)

# Подключение к локальному хранилищу
storage = shelve.open('education')


# Обработка команды /start
@bot.message_handler(commands=['start'])
def start_handler(message):
    messages.greeting_text(bot, message)
    start(message)


# Первый выбор пользователя
def start(message):
    messages.start_text(bot, message)
    bot.register_next_step_handler(message, first_choice_handler)


def first_choice_handler(message):
    text = message.text
    if text == 'Узнать подробнее о ПИШ':
        messages.about_aes_text(bot, message)
        bot.register_next_step_handler(message, first_choice_handler)
    elif text == 'Выбрать уровень образования':
        education_choice(message)
    else:
        another_message(message, first_choice_handler)


# Выбор уровня образования
def education_choice(message):
    messages.education_choice_text(bot, message)
    bot.register_next_step_handler(message, education_choice_handler)


def education_choice_handler(message):
    text = message.text
    if text not in text_info.education.keys():
        another_message(message, education_choice_handler)
    else:
        specialization_choice(message)


# Выбор специальности
def specialization_choice(message):
    messages.specialization_choice_text(bot, message)
    bot.register_next_step_handler(message, specialization_choice_handler)


def specialization_choice_handler(message):
    text = message.text
    if text not in text_info.education['Бакалавриат'] + text_info.education['Магистратура']:
        another_message(message, specialization_choice_handler)
    else:
        chat_id = message.chat.id
        # Сохранение специальности в локальное хранилище
        storage[str(chat_id)] = text
        questions(message)


# Выбор вопроса
def questions(message):
    messages.questions_text(bot, message)
    bot.register_next_step_handler(message, questions_handler)


def questions_handler(message):
    text = message.text
    if text == 'НЕТ НУЖНОГО ОТВЕТА':
        recipient(message)
    elif text not in text_info.questions:
        another_message(message, questions_handler)
    else:
        answer_question(message)


# Ответ на вопрос
def answer_question(message):
    chat_id = message.chat.id
    text = message.text
    if text == 'Правила приёма':
        path = '../docs/Правила приёма.pdf'
    else:
        # Считывание специальности из локального хранилища
        specialization = storage[str(chat_id)]
        path = f'../docs/{specialization}.json'
    # Ответ на вопрос
    response = LLM.LLM_chain(path, text)
    bot.send_message(
        chat_id=chat_id, 
        text=f'Ответ на вопрос \"{text}\" по специальности {specialization}:\n{response}'
    )
    # Возврат к этому же обработчику
    bot.register_next_step_handler(message, questions_handler)



# Выбор получателя письма
def recipient(message):
    messages.recipients_text(bot, message)
    bot.register_next_step_handler(message, recipient_handler)


def recipient_handler(message):
    text = message.text
    if text == text_info.back:
        questions_handler(message)
    elif text not in text_info.question_recipient:
        another_message(message, recipient)
    else:
        chat_id = message.chat.id
        # Добавление получателя в локальное хранилище
        storage[str(chat_id) + '_mail'] = [text]
        messages.first_last_name_text(bot, message)
        bot.register_next_step_handler(message, first_last_name)


# Обработка ввода имени и фамилии
def first_last_name(message):
    chat_id = message.chat.id
    text = message.text
    # Add first name and last name to local storage
    mail_info = storage[str(chat_id) + '_mail']
    mail_info.append(text)
    storage[str(chat_id) + '_mail'] = mail_info
    bot.send_message(chat_id, 'Укажи свой адрес электронной почты, на который будет отправлен ответ.')
    bot.register_next_step_handler(message, email)


# Обработка ввода почты
def email(message):
    chat_id = message.chat.id
    text = message.text
    # Add email to local storage
    mail_info = storage[str(chat_id) + '_mail']
    mail_info.append(text)
    storage[str(chat_id) + '_mail'] = mail_info
    bot.send_message(chat_id, 'Напиши свой вопрос.')
    bot.register_next_step_handler(message, open_question)


# Обработка ввода ответа
def open_question(message):
    chat_id = message.chat.id
    text = message.text
    # Get info from local storage
    mail_info = storage[str(chat_id) + '_mail']
    # Send mail
    bot.send_message(
        chat_id, 
        f'**to:** {mail_info[0]}\n**from:** {mail_info[1]}\n**email:** {mail_info[2]}\n**text:** {text}'
    )
    del storage[str(chat_id) + '_mail']
    bot.send_message(chat_id, 'Твой вопрос успешно отправлен.\n'
                    'Ответ скоро придет тебе на указанный адрес электронной почты.')
    bot.send_message(chat_id, 'ЖДЕМ ТЕБЯ В ПИШ!')
    start(message)


def another_message(message, next_step_handler):
    if message.text == '/start':
        start_handler(message)
    elif message.text == text_info.to_start:
        start(message)
    else:
        chat_id = message.chat.id
        bot.send_message(chat_id, 'Выбери, пожалуйста, один вариант из предложенных.')
        bot.register_next_step_handler(message, next_step_handler)


if __name__ == '__main__':
    bot.polling()

# Закрытие подключения к локальному хранилищу
storage.close()
