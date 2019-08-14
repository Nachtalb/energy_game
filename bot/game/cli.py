import json
import re
import sys
from json import JSONDecodeError
from typing import Dict, List
from urllib.error import HTTPError

from PyInquirer import prompt

from bot.game import EnergySession, Operator
from bot.game.utils import draw_banner


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
        options = {}
        if self.operator.logged_in:
            options['Start Bot'] = self.start
            options['Run once'] = self.run_once
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

    def run_once(self):
        result = self.operator.run_game()

        if not result:
            print('No ticket won.')
            return

        print('You have won!')

    def start(self):
        try:
            print()
            runner = self.operator.run()
            for iteration, result in enumerate(runner, 1):
                sys.stdout.write('\033[K')
                print(f'Iteration {iteration}', end='\r')
                if result:
                    print('\nYou have won!')
                    runner.close()
        except KeyboardInterrupt:
            pass
        finally:
            print('\nStopping')

    def login(self):
        tel_question = self.menu_item('tel', 'input', 'Please give me your cellphone number: +41')

        while True:
            self.tel = prompt(tel_question).get('tel')
            tel = re.sub('^(\+41|0)+', '', self.tel)

            if tel and not self.session.smstoken(tel):
                print(f'Could not initiate login with your number "{self.tel}"')
            else:
                break

        message = 'Please put in the code that was sent to your phone [{}/5]:'
        code_question = self.menu_item('code', 'input', message)
        tries = 1
        while True:
            code_question[0]['message'] = message.format(tries)
            code = prompt(code_question).get('code')

            if not code or not self.session.login(tel, code):
                print('Code seems to be incorrect, please try again.')
                tries += 1
            else:
                break

    def logout(self):
        self.session.logout()


def main():
    draw_banner('Energy Bot')
    debug = 'debug' in sys.argv
    menu = Menu()
    while menu.running:
        try:
            menu.main()
        except HTTPError as e:
            if not debug:
                try:
                    response_data = e.peek()
                    data = json.loads(response_data)
                    if 'message' in data and 'errorName' in data:
                        print(f'{data["errorName"]}: {data["message"]}')
                        continue
                except JSONDecodeError:
                    pass
                print('An error occurred please try again.')
                continue
            menu.running = False
            raise e
        except KeyboardInterrupt:
            menu.operator.save()
            menu.running = False
        except Exception as e:
            menu.operator.save()
            if debug:
                menu.running = False
                raise e
        finally:
            if not menu.running:
                print('Exit')
                break


if __name__ == "__main__":
    main()
