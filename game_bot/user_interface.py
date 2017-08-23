from collections import namedtuple
from typing import List

from . import EventHandler
from . import events

CLIListItem = namedtuple('CLIListItem', ['title', 'identifier', 'value'])


class CommandLineInterface:

    def __init__(self, event_handler: EventHandler, autostart: bool=None):
        self.ev = event_handler
        self.ev.add_handler(self)

        self.autostart = autostart or False

    def notify(self, event):
        if isinstance(event, events.InitEvent):
            if self.autostart:
                self.ev.notify(events.StartEvent())
            else:
                self.init()
        elif isinstance(event, events.StartEvent):
            self.wait_for_input()
        elif isinstance(event, events.QuitEvent):
            print('Goodbye')
        elif isinstance(event, events.WonEvent):
            print('Won :) - Phone Number: %s ', event.phone_number)
            self.ev.notify(events.StartEvent())
        elif isinstance(event, events.GameOverEvent):
            print('GameOver :(')
            self.ev.notify(events.StartEvent())
        elif isinstance(event, events.AddQuestionEvent) and event.choice is None:
            self.add_question(event.question, event.answers, bot_name=event.bot_name)

    def init(self):
        self.main_menu()

    def list_with_title(self, title: str, items: List[CLIListItem]) -> CLIListItem:
        item_template = '({identifier}) - {title}'

        print(title)
        for item in items:
            print(item_template.format(identifier=item.identifier.lower(), title=item.title))

        choice = ''
        while choice not in [item.identifier for item in items]:
            choice = input('Your choice: ')

        for item in items:
            if item.identifier == choice:
                return item

    def main_menu(self):
        self.ev.notify(events.PauseEvent())
        items = [
            CLIListItem(title='Start', identifier='s', value=events.StartEvent),
            CLIListItem(title='Add Question', identifier='a', value=events.AddQuestionEvent),
            CLIListItem(title='Quit', identifier='q', value=events.QuitEvent),
        ]

        choice = self.list_with_title('MainMenu', items)
        if choice.title == items[1].title:
            self.ask_for_question()
        else:
            self.ev.notify(choice.value())

    def add_question(self, question: str=None, answers: list=None, bot_name: str=None):
        items = [
            CLIListItem(title=answers[0], identifier='a', value=0),
            CLIListItem(title=answers[1], identifier='b', value=1),
            CLIListItem(title=answers[2], identifier='c', value=2),
            CLIListItem(title='Skip? (Restart Quiz)', identifier='s', value='skip'),
        ]

        choice = self.list_with_title('Questions: %s' % question, items)
        self.ev.notify(events.AddQuestionEvent(question=question, answers=answers, choice=choice.value,
                                               bot_name=bot_name))

    def ask_for_question(self):
        question, answer = None, None

        print('Question and Answer must be exactly what is shown on the https://game.energy.ch page.')

        while not question:
            question = input('Question: ')
        while not answer:
            answer = input('Answer: ')

        self.ev.notify(events.AddQuestionEvent(question=question, answers=[answer], choice=0))
        self.main_menu()

    def wait_for_input(self):
        commands = [
            ('m', 'main menu', self.main_menu),
            ('q', 'quit', lambda s=self: s.ev.notify(events.QuitEvent()))
        ]
        while True:
            input_ = input('Available commands %s and hit enter. \n' %
                           ''.join(['"{}"={}'.format(command[0], command[1]) for command in commands]))
            actions = [command[2] for command in commands if input_ == command[0]]
            if actions:
                actions[0]()
                break

