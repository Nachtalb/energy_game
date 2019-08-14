import base64
import json
import re
import sys
from contextlib import closing
from datetime import datetime
from http.cookiejar import MozillaCookieJar
from os import getcwd
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlencode, urlunsplit
from urllib.request import HTTPCookieProcessor, Request, build_opener

from PyInquirer import prompt

from bot.game.utils import draw_banner


class EnergySession:
    base_url = 'game.energy.ch'
    api_root = '/api'
    protocol = 'https'

    def __init__(self):
        cookie_file = Path(getcwd()) / 'cookies.txt'
        self.cookie_jar = MozillaCookieJar(str(cookie_file))
        self.cookie_jar.load()

        self.session = build_opener(HTTPCookieProcessor(self.cookie_jar))
        self.last_response = None
        self.token = None

    def smstoken(self, mobile: str) -> bool:
        endpoint = 'smstoken'

        data = {
            'mobile': mobile,
        }

        response_data = self._request(endpoint=endpoint, data=data, method='POST')
        return response_data.get('status') == 'ok'

    def login(self, mobile: str, token: str) -> bool:
        endpoint = f'smstoken/{token}'

        data = {
            'mobile': mobile,
        }

        response_data = self._request(endpoint=endpoint, data=data, method='PUT')
        return bool(response_data.get('token'))

    def _jwt_data(self) -> Dict:
        token = None
        for cookie in self.cookie_jar:
            if cookie.name != 'jwt-token':
                continue
            token = cookie.value
        if not token:
            return {}
        data = token.split('.')[1]
        return json.loads(base64.decodebytes(data.encode())) or {}

    @property
    def phone_number(self) -> str:
        return self._jwt_data().get('sub')

    @property
    def expiry(self) -> datetime or None:
        timestamp = self._jwt_data().get('exp')
        return datetime.utcfromtimestamp(timestamp) if timestamp else None

    def questions(self):
        endpoint = 'questions'

        return self._request(endpoint=endpoint)

    def logout(self):
        pass

    def _build_url(self, endpoint: str, parameters: Dict = None) -> str:
        query = urlencode(parameters or {})
        return urlunsplit((self.protocol, self.base_url, f'{self.api_root}/{endpoint}', query, ''))

    def _request(self, *, endpoint: str, data: Dict = None, params: Dict = None, method: str = None) -> Dict:
        method = method or 'GET'

        url = self._build_url(endpoint, params)

        encoded_data = urlencode(data).encode() if data else None
        request = Request(url, method=method, data=encoded_data)

        request.origin_req_host = f'{self.protocol}://{self.base_url}'
        self.last_response = self.session.open(request)
        self.cookie_jar.save()

        return json.load(self.last_response)


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

    def load_answers(self, answer_file: str or Path = None):
        path = (Path(answer_file) if answer_file else Path() / 'answers.txt').absolute()
        str_path = str(path)
        with closing(path.open()) as file:
            current_question = None
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
                    else:
                        answer = int(ids[0])
                    self.answers[current_question] = answer
                    current_question = None

    @property
    def logged_in(self):
        return self.session.expiry and self.session.expiry > datetime.utcnow()

    def save(self):
        self.session.cookie_jar.save()


class Menu:
    def __init__(self):
        self.session = EnergySession()
        self.operator = Operator(self.session, guess_randomly=True)
        self.running = True

        self.tel = ''

    def menu_item(self, name: str, type: str, text: str, **kwargs) -> List[Dict]:
        item = {
            'type': type,
            'name': name,
            'message': text,
        }

        item.update(kwargs)
        return [item]

    def main(self):
        options = {'Start Bot': self.start,}

        if self.operator.logged_in:
            options[f'Logout (+41{self.session.phone_number})'] = self.logout
        else:
            options['Login'] = self.login

        options['Exit'] = self.exit

        entries = self.menu_item('next', 'list', 'What do you want to do?', choices=options.keys())

        answer = prompt(entries)
        method = options.get(answer.get('next'), self.exit)
        method()

    def exit(self):
        self.operator.save()
        self.running = False

    def start(self):
        pass

    def login(self):
        tel_question = self.menu_item('tel', 'input', 'Please give me your cellphone number: +41')

        while True:
            self.tel = prompt(tel_question).get('tel')
            tel = re.sub('^(\+41|0)+', '', self.tel)

            if tel and not self.session.smstoken(tel):
                print(f'Could not initiate login with your number "{self.tel}"')
            else:
                break

        print('Energy will now send you a code.')

        code_question = self.menu_item('code', 'input', 'Please put in the code that was sent to your phone:')
        while True:
            code = prompt(code_question).get('code')

            if not code or not self.session.login(tel, code):
                print('Code seems to be incorrect, please try again.')
            else:
                break

    def logout(self):
        pass


def main():
    draw_banner('Energy Bot')

    menu = Menu()
    try:
        while menu.running:
            menu.main()
    except KeyboardInterrupt:
        menu.operator.save()
    except Exception as e:
        menu.operator.save()
        if 'debug' in sys.argv:
            raise e
    finally:
        print('Exit')


if __name__ == "__main__":
    main()
