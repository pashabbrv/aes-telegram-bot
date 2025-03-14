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
