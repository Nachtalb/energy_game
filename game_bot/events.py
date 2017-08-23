class Event:
    name = 'event'


class StartEvent(Event):
    name = 'start'


class QuitEvent(Event):
    name = 'start'


class AddQuestionEvent(Event):
    name = 'add_question'

    def __init__(self, question: str, answers: list, choice: int=None, bot_name: str=None):
        self.question = question
        self.answers = answers
        self.choice = choice
        self.bot_name = choice


class WonEvent(Event):
    name = 'won'

    def __init__(self, phone_number: str):
        self.phone_number = phone_number


class GameOverEvent(Event):
    name = 'game_over'


class InitEvent(Event):
    name = 'init_event'


class PauseEvent(Event):
    name = 'pause_event'
