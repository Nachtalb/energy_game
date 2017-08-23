from . import EventHandler
from . import events
from .utils import new_logger
from .utils import write_file
from bs4 import BeautifulSoup
from collections import namedtuple
from random import randint
from urllib.parse import urlencode
import codecs
import http.cookiejar
import json
import threading
import urllib.request

Webpage = namedtuple('Webpage', ['url', 'post', 'get', 'soup'])
URL_BASE = 'https://game.energy.ch/'


class BotManager:
    def __init__(self, event_handler: EventHandler, phone_number: str,  skip_unknown: str=None, bot_amount: int=None):
        self.logger = new_logger('GameBot', './game_bot.log')
        self.logger.info('Initiate GameBot')

        self.ev = event_handler
        self.ev.add_handler(self)

        self.bot_amount = bot_amount or 1
        self.threads = {}
        self.phone_number = phone_number
        self.questions_path ='./questions.json'

        if skip_unknown == 'normal':
            self.skip_unknown = BotThread.UNKNOWN_ASK
        elif skip_unknown == 'skip':
            self.skip_unknown = BotThread.UNKNOWN_SKIP
        elif skip_unknown == 'random':
            self.skip_unknown = BotThread.UNKNOWN_RANDOM

        with codecs.open(self.questions_path, 'r', 'utf-8') as fp:
            self.question_mapping = json.load(fp)

    def notify(self, event):
        if isinstance(event, events.StartEvent):
            for i in range(self.bot_amount):
                bot_name = 'bot-' + str(i)
                self.threads[bot_name] = threading.Timer(
                    1,
                    lambda s=self, name=bot_name:
                    BotThread(
                        name=name,
                        event_handler=s.ev,
                        phone_number=s.phone_number,
                        question_mapping=s.question_mapping,
                        unknown_action=s.skip_unknown
                    )
                )
                self.threads[bot_name].daemon = True
                self.threads[bot_name].start()
        elif isinstance(event, events.AddQuestionEvent) and isinstance(event.choice, int):
            self.save_question(event.question, event.answers, event.choice)

    def save_question(self, question, answers, choice):
        self.question_mapping.append({
            'question': question,
            'answer': answers[choice]
        })
        write_file(
            self.questions_path,
            json.dumps(self.question_mapping, ensure_ascii=False, indent=4, sort_keys=True)
        )


class BotThread(threading.Thread):
    UNKNOWN_ASK = 0
    UNKNOWN_SKIP = 1
    UNKNOWN_RANDOM = 2

    STATE_UNLOADED = 0
    STATE_LOADING = 1
    STATE_QUESTIONING = 2
    STATE_STOPPED = 3

    def __init__(self, name: str, event_handler: EventHandler, phone_number: str, question_mapping: list,
                 unknown_action: int=None):
        super(BotThread, self).__init__()

        self.name = name
        self.ev = event_handler
        self.ev.add_handler(self)
        self.phone_number = phone_number
        self.question_mapping = question_mapping
        self.unknown = unknown_action or self.UNKNOWN_ASK

        self.logger = new_logger(name, file_logger=False)

        self.skip_current_game = False
        self.state = self.STATE_UNLOADED
        self.current_page = None
        self.cookie_jar = None
        self.URLopener = None

        self.start_game()

    def notify(self, event):
        this_bot = getattr(event, 'bot_name', False)
        if this_bot:
            if isinstance(event, events.AddQuestionEvent) and event.choice == 'skip':
                self.skip_current_game = True
        elif isinstance(event, events.StartEvent):
            self.start_game()
        elif isinstance(event, events.QuitEvent):
            self.stop()

    def start_game(self):
        self.state = self.STATE_LOADING
        while self.state != self.STATE_STOPPED:
            try:
                self.logger.info('Start GameBot with - phone number: %s', self.phone_number)
                self.set_url_opener()
                self.set_cookie()
                self.load_html({'mobile': self.phone_number})
                self.questioning()
                self.skip_current_game = False
            except urllib.error.HTTPError as e:
                self.logger.warning('%s, restarting quiz.' % str(e))

    def stop(self):
        self.state = self.STATE_STOPPED
        self._stop()

    def set_url_opener(self):
        self.logger.debug('Setting URL Opener')
        self.cookie_jar = http.cookiejar.CookieJar()
        self.URLopener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))
        self.URLopener.addheaders.clear()
        self.URLopener.addheaders.append((
            'User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/60.0.3112.90 Safari/537.36'
        ))

    def set_cookie(self):
        self.logger.debug('Setting Cookie')
        self.URLopener.open(URL_BASE)
        cookie = [cookie for cookie in self.cookie_jar if cookie.name == 'PHPSESSID'][0]
        self.URLopener.addheaders.append(('Cookie', cookie.name + '=' + cookie.value))

    def load_html(self, post: dict=None, get: dict=None, uri: str=None):
        post_encoded = urlencode(post) if post else ''
        get_encoded = '?' + urlencode(get) if get else ''
        uri = uri.strip(' /?') if uri else ''
        full_url = URL_BASE + uri + get_encoded
        self.logger.debug('Load page - URL: %s, post: %s, get: %s', full_url, post_encoded, get_encoded)
        with self.URLopener.open(full_url, bytes(post_encoded, 'UTF-8')) as response:
            soup = BeautifulSoup(response.read(), 'html.parser')

        self.current_page = Webpage(url=full_url, post=post, get=get, soup=soup)

    def questioning(self):
        self.state = self.STATE_QUESTIONING

        questions_answers = {}
        while self.current_page.soup.select('form.question h1'):
            if self.skip_current_game:
                break

            question_text = self.current_page.soup.select('form.question h1')[0].text.strip()
            label_texts = [(label.text.strip(), label) for label in
                           self.current_page.soup.select('form.question .fields label')]

            for item in self.question_mapping:
                if question_text == item['question']:
                    questions_answers[question_text] = [answer[0] for answer in label_texts
                                                        if answer[0] != item['answer']]

                    for answer_tuple in label_texts:
                        if answer_tuple[0] == item['answer']:
                            self.logger.info('Question: %s, Answer: %s', item['question'], item['answer'])
                            questions_answers[question_text].append("* " + item['answer'])

                            value = answer_tuple[1].find_previous_sibling('input')['value'].strip()
                            self.load_html({'question': value})
                            break
                    break
            else:
                self.logger.warning('Question unknown')
                if self.unknown == self.UNKNOWN_ASK:
                    self.ev.notify(events.AddQuestionEvent(
                        question=question_text,
                        answers=[answer_tuple[0] for answer_tuple in label_texts],
                        bot_name=self.name
                    ))
                elif self.unknown == self.UNKNOWN_SKIP:
                    self.skip_current_game = True
                    break
                elif self.unknown == self.UNKNOWN_RANDOM:
                    random = randint(1, 3)
                    random_answer = label_texts[random - 1][0]
                    self.logger.warning('Random value - question: %s, answer: %s', question_text, random_answer)

                    questions_answers[question_text] = [answer_tuple[0] for answer_tuple in label_texts
                                                        if answer_tuple[0] != random_answer]
                    questions_answers[question_text].append("* " + random_answer)

                    self.load_html({'question': random})
        else:
            self.questions_finished(questions_answers)

    def questions_finished(self, questions_answers):
        if self.current_page.soup.select('#mood-bad'):
            self.logger.warning('Game Over: Some off the questions were false. See error.log for further info.')
            error_logger = new_logger('AnswerWrong', './error.log', console_logger=False)
            error_logger.warning('Some of these answers were wrong:')

            for question, answer in questions_answers.items():
                error_logger.warning('{:<75}: {}'.format(question, answer))

        elif self.current_page.soup.select('#mood-good'):
            self.logger.info('You made it through the quiz. Now a random number will be drawn.')

            self.load_html(post={'site': 'win'})
            self.load_html(get={'ticket': randint(0, 11)})

            if self.current_page.soup.select('[src=images/esff_ticket_wrong.png]'):
                self.logger.warning('Sadly you did not win this round.')
            else:
                self.logger.warning('YES congratulations you have won look at your phone if you got the sms.')
