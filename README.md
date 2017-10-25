# Energy Game

Bot for [game.energy.ch](https://game.energy.ch) by [@Nachtalb](https://github.com/Nachtalb).


## Installation

Make sure you have python 3.6 or higher installed.

Clone and cd to the git repo
```bash
$ git clone https://github.com/Nachtalb/energy_game.git [some path]
$ cd [some path]
```

Instead of the old `pip` with `requirements.txt` I use the new and fancy `pipenv` with `pipfile`. If you read the intro
to [pipenv](https://github.com/pypa/pipfile) and [pipfile](https://docs.pipenv.org) you will understand why I use it.

With this info we now install our virtualenv with:
```bash
$ pip install pipenv  # Install pipenv
$ pipenv --three      # Create virtualeenv from your python3 installation
$ pipenv install      # Install all requirements
$ pipenv shell        # Spawn shell for your pipenv virtualenv
```

The app is now installed and you can use it as described in the [usage](#usage) section.

#### Example

```
$ git clone https://github.com/Nachtalb/energy_game.git ~/projects/energy_game
$ cd ~/projects/energy_game
$ pip install pipenv
$ pipenv --three
$ pipenv install
$ pipenv shell

$ python main.py 0491570156 -a -s random -c 4
```

## Usage

You can also use some commands on the run. Type the corresponding letter and hit <kbd>enter</kbd>.

- `m` to open the main menu
- `q` to quit the game

```
usage: main.py [-h] [-s {skip,random,normal}] [-a] phone_number

positional arguments:
  phone_number          The phone number to send the "you have won" sms to

optional arguments:
  -h, --help            show this help message and exit
  -s {skip,random,normal}, --skip {skip,random,normal}
                        Skip unknown questions, answer them randomly or wait
                        for input (default).
  -a, --autostart       Autostart the quize, default False
  -c, --bot-amount      Amount of bots to start (default 1)
```

## ToDo

- [ ] Pause bot
- [ ] Change settings interface
- [x] Add multithreading to make multiple bot instances without the need to start the app multiple times

## Contributions

I know that some answers are wrong. If you know which or some questions were not added yet please make an issue or a pull request.
For any other contributions follow the code style of this project.
Those are:
- [Pep8](https://www.python.org/dev/peps/pep-0008/) with the exception of a line length of 120 characters

## Compatibility

[game.energy.ch](https://game.energy.ch) 2017

## Built with

- [Python 3.6](https://www.python.org/)
- [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

## Credits

[@Nachtalb](https://github.com/Nachtalb)

## Copyright

Published under the [Beerware Licence](https://github.com/Nachtalb/energy_game/blob/master/LICENSE.txt)
