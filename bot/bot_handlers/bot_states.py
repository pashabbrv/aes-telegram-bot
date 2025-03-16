from telebot.handler_backends import State, StatesGroup


class StartState(StatesGroup):
    start = State()
    info = State()


class MainMenuState(StatesGroup):
    main = State()


class SpecializationState(StatesGroup):
    main_choice = State()
    specialization = State()
    question = State()


class QuestionState(StatesGroup):
    ask_question = State()
    wait_answer = State()
