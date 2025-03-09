from telebot import types

import text_information as text_info


def get_bot_info(func):
    def wrapper(bot, message):
        return func(bot, message.chat.id, message.text)
    return wrapper


@get_bot_info
def greeting_text(bot, chat_id, text):
    bot.send_message(chat_id, 'Приветствуем тебя в ПИШ!')


@get_bot_info
def start_text(bot, chat_id, text):
    # Создание клавиатуры с вариантами ответов
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*['Узнать подробнее о ПИШ', 'Выбрать уровень образования'], row_width=2)
    # Отправка сообщения вместе с клавиатурой
    bot.send_message(
        chat_id=chat_id,
        text='Выбирай интересующие тебя темы, чтобы узнать о \"Передовой инженерной школе\" подробнее.',
        reply_markup=keyboard
    )


@get_bot_info
def about_aes_text(bot, chat_id, text):
    # Вывод полной информации о ПИШ
    bot.send_message(chat_id, 'Здесь содержится развёрнутая информация о ПИШ.')


@get_bot_info
def education_choice_text(bot, chat_id, text):
    # Выбор уровня образования
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*text_info.education.keys(), text_info.to_start, row_width=2)
    bot.send_message(
        chat_id=chat_id,
        text='Выбери уровень образования, на котором ты собираешься обучаться.',
        reply_markup=keyboard
    )


@get_bot_info
def specialization_choice_text(bot, chat_id, text):
    # Выбор уровня образования
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*text_info.education[text], text_info.to_start, row_width=1)
    bot.send_message(
        chat_id=chat_id,
        text='Выбери специальность, о которой хочешь узнать больше.',
        reply_markup=keyboard
    )


@get_bot_info
def questions_text(bot, chat_id, text):
    # Создание вариантов из списка вопросов
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*text_info.questions, 'НЕТ НУЖНОГО ОТВЕТА', text_info.to_start, row_width=1)
    bot.send_message(
        chat_id=chat_id,
        text='Выбери, что тебя интересует.',
        reply_markup=keyboard
    )


@get_bot_info
def recipients_text(bot, chat_id, text):
    # Создание вариантов из списка вопросов
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*text_info.question_recipient, text_info.back, row_width=1)
    bot.send_message(
        chat_id=chat_id,
        text='Выбери, кому ты хочешь задать вопрос.',
        reply_markup=keyboard
    )


@get_bot_info
def first_last_name_text(bot, chat_id, text):
    # Отключение клавиатуры с выбором вариантов ответа
    remove_keyboard = types.ReplyKeyboardRemove()
    bot.send_message(
        chat_id=chat_id, 
        text=f'Укажи свою фамилию и имя.',
        reply_markup=remove_keyboard
    )