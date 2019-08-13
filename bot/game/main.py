import json
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
            self.session.check_login()
        except URLError:
            return False

    def save(self):
        self.session.cookie_jar.save()


class Menu:
    def __init__(self):
        self.session = EnergySession()
        self.operator = Operator(self.session)
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
        }

        if self.operator.logged_in:
            options['Logout'] = self.logout
        else:
            options['Login'] = self.login

        entries = self.menu_item('next', 'list', 'What do you want to do?', choices=options.keys())

        answer = prompt(entries)
        method = options.get(answer.get('next'))
        if not method:
            self.exit()
            return
        method()

    def exit(self):
        self.operator.save()

    def start(self):
        pass

    def login(self):
        tel_question = self.menu_item('tel', 'input', 'Please give me your cellphone number:')
        self.tel = None
        while not self.tel:
            self.tel = prompt(tel_question).get('tel')

        print(f'Your Number: {self.tel}')
        self.session.request_login_token(self.tel)

        print('Energy will now send you a code')

        code_question = self.menu_item('code', 'input', 'Please put in the code that was sent to your phone:')
        code = None
        while not code:
            code = prompt(code_question).get('code')

        self.session.login(self.tel, code)
        self.main()

    def logout(self):
        pass


def main():
    draw_banner('Energy Bot')

    menu = Menu()
    try:
        menu.main()
    except KeyboardInterrupt:
        menu.operator.save()
        print('Exit')
    except Exception as e:
        menu.operator.save()
        raise e


if __name__ == "__main__":
    main()
