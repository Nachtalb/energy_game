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
import os
import urllib.request

Webpage = namedtuple('Webpage', ['url', 'post', 'get', 'soup'])


class GameBot:
    URL_BASE = 'https://game.energy.ch/'

    def __init__(self, event_handler: EventHandler, phone_number: str, questions_path: str=None,
                 current_html_path: str=None, error_log_path: str=None, skip_unknown: str=None):
        self.logger = new_logger('GameBot', './game_bot.log')
        self.logger.info('Initiate GameBot')

        self.ev = event_handler
        self.ev.add_handler(self)

        self.skip = False  # Used to skip question
        self.ongoing = True
        self.phone_number = phone_number
        self.questions_path = questions_path or './questions.json'
        self.current_html_path = current_html_path or './game.html'
        self.error_log_path = error_log_path or './error.log'
        self.skip_unknown = skip_unknown if skip_unknown in ['normal', 'skip', 'random'] else 'normal'

        if os.path.isfile(self.current_html_path):
            os.remove(self.current_html_path)

        self.cookie_jar = None
        self.URLopener = None

        self.current_site = None
        with codecs.open(self.questions_path, 'r', 'utf-8') as fp:
            self.question_mapping = json.load(fp)

    def notify(self, event):
        if isinstance(event, events.StartEvent):
            self.start()
        elif isinstance(event, events.QuitEvent):
            self.ongoing = False
        elif isinstance(event, events.AddQuestionEvent) and event.choice == 'skip':
            self.skip = True
        elif isinstance(event, events.AddQuestionEvent) and isinstance(event.choice, int):
            self.add_question(event.question, event.answers, event.choice)

    def start(self):
        while self.ongoing:
            try:
                self.logger.info('Start GameBot with - phone number: %s, skip: %s', self.phone_number, self.skip_unknown)
                self.set_url_opener()
                self.set_cookie()
                self.load_html({'mobile': self.phone_number})
                self.questioning()
                self.skip = False
            except urllib.error.HTTPError:
                self.logger.warning('Server had an error, restarting quiz.')

    def set_url_opener(self):
        self.logger.debug('Setting URL Opener')
        self.cookie_jar = http.cookiejar.CookieJar()
        self.URLopener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))
        self.URLopener.addheaders.clear()
        self.URLopener.addheaders.append(
            ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/60.0.3112.90 Safari/537.36')
        )

    def set_cookie(self):
        self.logger.debug('Setting Cookie')
        self.URLopener.open(self.URL_BASE)
        cookie = [cookie for cookie in self.cookie_jar if cookie.name == 'PHPSESSID'][0]
        self.URLopener.addheaders.append(('Cookie', cookie.name + '=' + cookie.value))

    def load_html(self, post: dict=None, get: dict=None, uri: str=None):
        post_encoded = urlencode(post) if post else ''
        get_encoded = '?' + urlencode(get) if get else ''
        uri = uri.strip(' /?') if uri else ''
        full_url = self.URL_BASE + uri + get_encoded
        self.logger.debug('Load page - URL: %s, post: %s, get: %s', full_url, post_encoded, get_encoded)
        with self.URLopener.open(full_url, bytes(post_encoded, 'UTF-8')) as response:
            soup = BeautifulSoup(response.read(), 'html.parser')
            write_file(self.current_html_path, soup.prettify())

        self.current_site = Webpage(url=full_url, post=post, get=get, soup=soup)

    def get_question_from_html(self):
        pass

    def add_question(self, question: str, answers: list, choice: int):
        self.logger.info('Add new question: %s - %s', question, answers[choice])

        self.question_mapping.append({'question': question, 'answer': answers[choice]})
        write_file(self.questions_path, json.dumps(self.question_mapping, ensure_ascii=0, indent=4, sort_keys=1))

    def questioning(self):
        questions_answers = []
        while self.current_site.soup.select('form.question h1'):
            if self.skip:
                break

            question_text = self.current_site.soup.select('form.question h1')[0].text.strip()
            label_tags = self.current_site.soup.select('form.question .fields label')

            for item in self.question_mapping:
                if question_text == item['question']:
                    for label_tag in label_tags:
                        if label_tag.text.strip() == item['answer']:
                            questions_answers.append((item['question'], item['answer']))
                            value = label_tag.find_previous_sibling('input')['value'].strip()
                            self.logger.info('Question: %s, Answer: %s', item['question'], item['answer'])
                            self.load_html({'question': value})
                            break
                    break
            else:
                if self.skip_unknown == 'normal':
                    self.logger.warning('No entry for question available.')
                    self.ev.notify(
                        events.AddQuestionEvent(question=question_text, answers=[label.text for label in label_tags]))
                elif self.skip_unknown == 'skip':
                    self.logger.warning('Question is unknown, skip question')
                    self.skip = True
                    break
                elif self.skip_unknown == 'random':
                    random = randint(1, 3)
                    self.logger.warning('Question is unknown, take random value - question: %s, answer: %s',
                                        question_text, label_tags[random - 1].text)
                    self.load_html({'question': random})
        else:
            if self.current_site.soup.select('#mood-bad'):
                self.logger.warning('Game Over: Some off the questions were false. See error.log for further info.')
                error_logger = new_logger('AnswerWrong', self.error_log_path, console_logger=False)
                error_logger.warning('Some of these answers were wrong:')
                for item in questions_answers:
                    error_logger.warning(item)
            if self.current_site.soup.select('#mood-good'):
                self.logger.info('You made it through the quiz. Now a random number will be drawn.')
                self.load_html(post={'site': 'win'})
                self.load_html(get={'ticket': randint(0, 11)})
                if self.current_site.soup.select('[src=images/esff_ticket_wrong.png]'):
                    self.logger.warning('Sadly you did not win anything this round.')
                else:
                    self.logger.warning('YES congratulations you have won look at your phone if you got the sms.')
