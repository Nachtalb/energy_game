import json
import re
import sys
from http.cookiejar import MozillaCookieJar
from os import getcwd
from pathlib import Path
from typing import Dict, List
from urllib.error import URLError
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

        self.token = response_data.get('token')
        return bool(self.token)

    def logout(self):
        pass

    def _build_url(self, endpoint: str, parameters: Dict = None) -> str:
        query = urlencode(parameters or {})
        return urlunsplit((self.protocol, self.base_url, f'{self.api_root}/{endpoint}', query, ''))

    def _request(self, *, endpoint: str, data: Dict = None, params: Dict = None, method: str = None) -> Dict:
        method = method or 'GET'

        url = self._build_url(endpoint, params)

        encoded_data = urlencode(data).encode()
        request = Request(url, method=method, data=encoded_data)

        request.origin_req_host = f'{self.protocol}://{self.base_url}'
        self.last_response = self.session.open(request)
        self.cookie_jar.save()

        return json.load(self.last_response)

class Operator:
    def __init__(self, session: EnergySession):
        self.session = session

    @property
    def logged_in(self):
        try:
            return False
        except URLError:
            return False

    def save(self):
        self.session.cookie_jar.save()


class Menu:
    def __init__(self):
        self.session = EnergySession()
        self.operator = Operator(self.session)
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
        options = {
            'Start Bot': self.start,
            'Login': self.login,
            'Exit': self.exit,
        }

        if self.operator.logged_in:
            options['Logout'] = self.logout
        else:
            options['Login'] = self.login

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
