from game_bot import CommandLineInterface
from game_bot import EventHandler
from game_bot import GameBot
from game_bot.events import InitEvent
from game_bot.events import QuitEvent
import argparse
import sys

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phone_number', help='The phone number to send the "you have won" sms to', type=str)
    parser.add_argument('-s', '--skip',  action='store', default='normal', choices=['skip', 'random', 'normal'],
                        help='Skip unknown questions, answer them randomly or wait for input (default).', type=str)
    parser.add_argument('-a', '--autostart',  action='store_true', help='Autostart the quize, default False')
    args = parser.parse_args()
    event_handler = EventHandler()
    try:
        game_bot = GameBot(event_handler, args.phone_number, skip_unknown=args.skip)
        user_interface = CommandLineInterface(event_handler, autostart=args.autostart)
        event_handler.notify(InitEvent())
    except KeyboardInterrupt:
        event_handler.notify(QuitEvent())
        sys.exit()
