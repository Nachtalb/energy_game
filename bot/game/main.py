from http.client import HTTPResponse
from http.cookiejar import MozillaCookieJar
from os import getcwd
from pathlib import Path
from plistlib import Data
from typing import Dict
from urllib import request
from urllib.error import URLError

from PyInquirer import prompt

from bot.game.utils import draw_banner


class EnergySession:
    def __init__(self):
        cookie_file = Path(getcwd()) / 'cookies.txt'
        cookie_jar = MozillaCookieJar(str(cookie_file))
        cookie_jar.load()

        self.session = request.build_opener(request.HTTPCookieProcessor(cookie_jar))

    def check_login(self) -> bool:
        pass

    def login(self) -> bool:
        pass

    def logout(self):
        pass

    def get(self, url: str, data: Dict = None) -> HTTPResponse:
        pass

    def post(self, url: str, data: Data = None) -> HTTPResponse:
        pass


class Operator:
    def __init__(self):
        self.session = EnergySession()

    @property
    def logged_in(self):
        try:
            self.session.check_login()
        except URLError:
            return False


class Menu:
    def __init__(self):
        self.operator = Operator()

    def main(self):
        options = {
            'Start Bot': self.start,
            'Login': self.login,
        }

        if self.operator.logged_in:
            options['Logout'] = self.logout
        else:
            options['Login'] = self.login

        entries = [
            {
                'type': 'list',
                'name': 'next',
                'message': 'What do you want to do?',
                'choices': options.keys(),
            }
        ]

        answer = prompt(entries)
        method = options.get(answer['next'])
        method()

    def start(self):
        pass

    def login(self):
        pass

    def logout(self):
        pass


def main():
    draw_banner('Energy Bot')

    menu = Menu()
    menu.main()


if __name__ == "__main__":
    main()
