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
    ask_manager = State()


class QuestionState(StatesGroup):
    ask_question = State()
    wait_answer = State()


class FeedbackState(StatesGroup):
    main = State()


class AnswerState(StatesGroup):
    enter_id = State()
    enter_answer = State()


class EngineeringCompetitionState(StatesGroup):
    main_choice = State()
    details_and_rules = State()
    all_directions = State()
    direction = State()
    ask_question = State()
