from http.client import HTTPResponse
from http.cookiejar import MozillaCookieJar
from os import getcwd
from pathlib import Path
from plistlib import Data
from typing import Dict, List
from urllib import request
from urllib.error import URLError

from PyInquirer import prompt

from bot.game.utils import draw_banner


class EnergySession:
    def __init__(self):
        cookie_file = Path(getcwd()) / 'cookies.txt'
        self.cookie_jar = MozillaCookieJar(str(cookie_file))
        self.cookie_jar.load()

        self.session = request.build_opener(request.HTTPCookieProcessor(self.cookie_jar))

    def check_login(self) -> bool:
        pass

    def login(self, tel: str, token: str) -> bool:
        pass

    def request_login_token(self, tel: str) -> bool:
        pass

    def logout(self):
        pass

    def get(self, url: str, data: Dict = None) -> HTTPResponse:
        pass

    def post(self, url: str, data: Data = None) -> HTTPResponse:
        pass


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
