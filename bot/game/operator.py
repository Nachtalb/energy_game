import re
from contextlib import closing
from datetime import datetime
from pathlib import Path
from random import choice
from typing import Dict, Generator, List

from bot.game import EnergySession


class Operator:
    def __init__(self, session: EnergySession, answers: Dict = None, answer_file: str or Path = None,
                 guess_randomly: bool = False):
        self.session = session
        self.guess_randomly = guess_randomly
        if answers and answer_file:
            raise AttributeError('"answers" and "answer_file" are mutually exclusive.')

        self.answers = answers or {}
        if not self.answers:
            self.load_answers(answer_file)

    @property
    def logged_in(self) -> bool:
        return self.session.expiry and self.session.expiry > datetime.utcnow()

    def run(self) -> Generator[bool, None, None]:
        try:
            while True:
                yield self.run_game()
        finally:
            pass

    def run_game(self) -> bool:
        questions = self.session.questions()
        answers = list(self.answers_for_questions(questions))
        won = self.session.check_questions(answers)
        return won

    def save(self):
        self.session.cookie_jar.save()

    def answers_for_questions(self, questions: List[Dict]) -> List[int]:
        for question in questions:
            yield self.answer_to_question(question)

    def answer_to_question(self, question: Dict) -> int:
        answer = self.answers[question['id']]
        if answer is None and self.guess_randomly:
            return choice([0, 1, 2])
        elif answer is None:
            raise KeyError(f'No know answer found to question {question["id"]}')

        answer = answer.lower()
        for index, option in enumerate(question['answers']):
            if answer == option['text'].lower():
                return index

        if self.guess_randomly:
            return choice([0, 1, 2])
        else:
            raise KeyError(f'No fitting answer found to question {question["id"]}')

    def load_answers(self, answer_file: str or Path = None):
        path = (Path(answer_file) if answer_file else Path() / 'answers.txt').absolute()
        str_path = str(path)
        with closing(path.open()) as file:
            current_question = None
            current_options = {}
            for line_nr, line in enumerate(file.readlines(), 1):
                line = line.strip().lower()
                error_line = (str_path, line_nr, None, None)
                if line.startswith('question'):
                    ids = re.findall('\[(\d+)\]', line)
                    if not ids:
                        raise SyntaxError('Question ID missing', error_line)
                    elif int(ids[0]) in self.answers:
                        raise SyntaxError(f'Duplicate Question', error_line)
                    current_question = int(ids[0])

                elif line.startswith('option'):
                    ids = re.findall('(\d)\s*:', line)
                    text = re.findall(':(.*)', line)
                    if not text:
                        raise SyntaxError(f'Option is missing', error_line)
                    elif not ids:
                        raise SyntaxError(f'Option ID is missing', error_line)
                    elif not current_question:
                        raise SyntaxError(f'Option found but no connected question for it', error_line)
                    elif int(ids[0]) not in [1, 2, 3]:
                        raise SyntaxError(f'Option ID must be either 1, 2 or 3', error_line)
                    current_options[int(ids[0]) - 1] = text[0].strip()

                elif line.startswith('answer'):
                    ids = re.findall('(\d+)', line)
                    if not ids:
                        if not self.guess_randomly:
                            raise SyntaxError(f'Answer missing', error_line)
                        answer = None
                    elif not current_question:
                        raise SyntaxError(f'Answer found but no connected question for it', error_line)
                    elif int(ids[0]) not in [1, 2, 3]:
                        raise SyntaxError(f'Answer must be either 1, 2 or 3', error_line)
                    elif len(current_options) != 3:
                        raise SyntaxError(f'Answer found but wrong amount of options {len(current_options)} instead of 3',
                                          error_line)
                    else:
                        answer = int(ids[0]) - 1
                    self.answers[current_question] = current_options.get(answer)
                    current_question = None
                    current_options = {}
