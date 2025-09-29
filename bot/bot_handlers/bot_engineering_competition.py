from telebot import TeleBot, types

from .bot_main_menu import main_menu
from .bot_states import MainMenuState, EngineeringCompetitionState
from ..managers import competition_manager
from ..text_information import *

def register_commands(bot: TeleBot):
    '''Регистрация последовательности действий для инженерного конкурса'''

    # Обработчки, вызываемый при нажатии "Инженерный конкурс"
    @bot.message_handler(
        state=MainMenuState.main,
        func=lambda msg: msg.text == 'Инженерный конкурс',
    )
    def main_handler(message):
        main_choice(message)
    

    # Основной выбор в разделе
    def main_choice(message):
        bot.set_state(message.from_user.id, EngineeringCompetitionState.main_choice, message.chat.id)
        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        ).add('Узнать подробности и правила', 'Какие есть направления?', 'Зарегистрироваться', 'Задать вопрос о конкурсе', BACK, row_width=2)
        bot.send_message(
            chat_id=message.chat.id,
            text='''Хочешь не просто поступить в лучшую инженерную школу, а гарантировать себе место в ней? Участвуй в нашем инженерном конкурсе!
Это твой шанс:
✅ Решить реальную инженерную задачу от ведущих российских компаний!
✅ Получить дополнительные баллы при поступлении в ЛЭТИ. Победа или призовое место = твое преимущество перед другими абитуриентами.
✅ Погрузиться в мир современной инженерии еще до окончания школы, поработать в наших лабораториях и познакомиться с будущими наставниками.
Выбирай направление, регистрируйся и докажи, что ты — инженер нового поколения!
''',
            reply_markup=keyboard
        )
    

    @bot.message_handler(
        state=EngineeringCompetitionState.main_choice,
        func=lambda msg: msg.text == BACK
    )
    def back_to_main_menu(message):
        main_menu(bot, message)
    

    # Подробности и правила конкурса
    @bot.message_handler(
        state=EngineeringCompetitionState.main_choice,
        func=lambda msg: msg.text == 'Узнать подробности и правила'
    )
    def find_out_the_details_and_rules_handler(message):
        bot.set_state(message.from_user.id, EngineeringCompetitionState.details_and_rules, message.chat.id)
        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        ).add('Какие есть направления?', 'Зарегистрироваться', BACK, row_width=2)
        bot.send_message(
            chat_id=message.chat.id,
            text='''Цель конкурса: "Дать школьникам возможность проявить инженерные навыки, решить реальную задачу и получить льготы при поступлении."
Для кого: Учащиеся 9-11 классов.
Стоимость: участие бесплатное!
Этапы конкурса:
Регистрация: (до 11 октября). Подача заявки через [яндекс-форму](https://forms.yandex.ru/cloud/68d4df0849363921c75c2e7e/).
Отборочный этап: (до 02 ноября). Выполнение тестовых заданий и задач с открытым решением по математике, физике и информатике (заочно онлайн).
Образовательный блок: (с 3 по 23 ноября). Подготовка к решению конкурсных задач.
Очный этап (29-30 ноября). Решение инженерных задач по направлениям Электроника, робототехника, приборостроения.
Подведение итогов и награждение: Победители и призеры получают памятные подарки и дипломы, дающие право на дополнительные баллы в индивидуальные достижения при поступлении в ЛЭТИ.
''',
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    

    # Направления на конкурсе
    @bot.message_handler(
        state=[EngineeringCompetitionState.main_choice, EngineeringCompetitionState.details_and_rules],
        func=lambda msg: msg.text == 'Какие есть направления?'
    )
    def directions_handler(message):
        directions_choice(message)
    

    def directions_choice(message):
        bot.set_state(message.from_user.id, EngineeringCompetitionState.all_directions, message.chat.id)
        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        ).add('Электроника', 'Робототехника', 'Приборостроение', BACK, row_width=2)
        bot.send_message(
            chat_id=message.chat.id,
            text='Наш конкурс проходит по трем направлениям, соответствующим программам Передовой инженерной школы. Выбери то, что тебе ближе!',
            reply_markup=keyboard
        )
    

    @bot.message_handler(
        state=[EngineeringCompetitionState.details_and_rules, EngineeringCompetitionState.all_directions],
        func=lambda msg: msg.text == BACK
    )
    def back_to_main_choice(message):
        main_choice(message)
    

    # Конкретное направление на конкурсе
    @bot.message_handler(
        state=EngineeringCompetitionState.all_directions,
        func=lambda msg: msg.text in ['Электроника', 'Робототехника', 'Приборостроение']
    )
    def direction_handler(message):
        direction_message(message)
    

    def direction_message(message):
        bot.set_state(message.from_user.id, EngineeringCompetitionState.direction, message.chat.id)
        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        ).add('Зарегистрироваться', BACK, row_width=1)
        answer_text = ''
        if message.text == 'Электроника':
            answer_text = '''Цифровая схемотехника: Оживи электронные схемы!
Забудь о виртуальных симуляторах! Здесь ты будешь создавать реальные устройства своими руками, от идеи до работающего прототипа. Это направление — фундамент всего цифрового мира: от смартфона до сложнейших процессоров.
•	Магия превращения кода и схем в физические устройства, которые можно потрогать.
•	Практика с самого начала: ты сразу погружаешься в процесс создания, а не только в теорию.
Идеально для тебя, если ты: любишь пайку, хочешь понять, как «думают» компьютеры, и мечтаешь создавать своими руками то, что работает наглядно и понятно.'''
        elif message.text == 'Робототехника':
            answer_text = '''Коллаборативная робототехника: Стань напарником для робота!
Представь, что ты программируешь не просто машину, а умного помощника, который работает рядом с тобой в одной команде. Это не фантастика — это коллаборативная робототехника! Ты будешь работать на самых современных промышленных манипуляторах, которые безопасны для взаимодействия с человеком.
Что тебя ждет:
•	Программирование реальных промышленных роботов, которые используются на заводах по всему миру.
•	Создание интеллекта для «железной руки»: ты научишь робота видеть, думать и действовать автономно.
•	Работа в команде «человек-робот»: ты увидишь, как твои алгоритмы позволяют роботу и человеку работать вместе, дополняя друг друга.
Идеально для тебя, если ты: видишь будущее в автоматизации, любишь, когда код приводит в движение мощные механизмы, и хочешь разобраться в искусственном интеллекте для реальных задач.
Идеальный формат — команда из двух человек, но участвовать можно и в одиночку, мы поможем найти единомышленника.'''
        else:
            answer_text = '''Создай устройство с нуля — от идеи до корпуса!
Если тебе мало просто спаять плату и хочешь создать полноценный, готовый к работе прибор — это твое направление! Здесь ты пройдешь весь цикл создания современного устройства: от разработки схемы и прототипа до проектирования его собственного корпуса.
Что тебя ждет:
•	Полный цикл разработки: ты не только создашь «начинку» устройства, но и спроектируешь для него индивидуальный корпус.
•	Работа на стыке механики и электроники: от идеи и расчетов до пайки и 3D-моделирования.
•	Создание реально работающих измерительных систем, которые можно использовать в жизни.
Идеально для тебя, если ты: любишь доводить начатое до конца, тебе интересно, как устроены приборы вокруг.
Идеальный формат — команда из двух человек, где один может сосредоточиться на электронной «начинке», а другой — на механике и дизайне корпуса. Можно участвовать и в одиночку, мы поможем найти единомышленника!'''
        bot.send_message(
            chat_id=message.chat.id,
            text=answer_text,
            reply_markup=keyboard
        )
    

    @bot.message_handler(
        state=EngineeringCompetitionState.direction,
        func=lambda msg: msg.text == BACK
    )
    def back_to_directions_choice(message):
        directions_choice(message)
    

    @bot.message_handler(
        state=[EngineeringCompetitionState.direction, EngineeringCompetitionState.main_choice, EngineeringCompetitionState.details_and_rules],
        func=lambda msg: msg.text == 'Зарегистрироваться'
    )
    def back_to_main_choice(message):
        bot.send_message(
            chat_id=message.chat.id,
            text='Зарегистрируйся и обеспечь себе преимущество!\n[Ссылка на анкету](https://forms.yandex.ru/cloud/68d4df0849363921c75c2e7e/)',
            parse_mode='Markdown'
        )
    

    @bot.message_handler(
        state=EngineeringCompetitionState.main_choice,
        func=lambda msg: msg.text == 'Задать вопрос о конкурсе'
    )
    def ask_question_handler(message):
        ask_question_message(message)
    

    def ask_question_message(message):
        bot.set_state(message.from_user.id, EngineeringCompetitionState.ask_question, message.chat.id)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(START)
        bot.send_message(
            chat_id=message.chat.id, 
            text=f'Есть вопрос? Напиши нам!',
            reply_markup=keyboard
        )
    

    @bot.message_handler(
        state=EngineeringCompetitionState.ask_question
    )
    def ask_manager_handler(message):
        if message.text == START:
            main_menu(bot, message)
        else:
            try:
                bot.send_message(
                    chat_id=competition_manager, 
                    text=f'Вопрос от пользователя {message.chat.id}:\n\n{message.text}',
                )
                bot.send_message(
                    chat_id=message.chat.id, 
                    text='Твой вопрос успешно отправлен. Вскоре куратор конкурса даст на него ответ.',
                )
            except Exception:
                bot.send_message(
                    chat_id=message.chat.id, 
                    text='К сожалению, вопрос отправить не удалось.',
                )
            ask_question_message(message)
