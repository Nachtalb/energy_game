# Energy Game

Bot for [game.energy.ch](https://game.energy.ch) by [@Nachtalb](https://github.com/Nachtalb).

## Usage

Make sure you have python 3.6 or higher installed.

1. Clone and cd to the git repo
    ```
    $ git clone https://github.com/Nachtalb/energy_game.git [some path]
    $ cd [some path]
    ```

2. Make a virtualenv
    ```
    $ virtualenv -p python3.6 [your venv name]
    ```
    If `python3.6` does not work, locate the your python3.6 executable and
    use this path instead.
3. Start virtualenv
    ```
    $ source [your venv name]/bin/activate
    ```
4. Install requirements
    ```
    $ pip install -r requirements.txt
    ```
5. Use the app
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

#### Example

```
$ git clone https://github.com/Nachtalb/energy_game.git ~/projects/energy_game
$ cd ~/projects/energy_game
$ virtualenv -p python3.6 venv
$ source venv/bin/activate
$ pip install -r requirements.txt

$ python main.py 0491570156 -a -s random -c 4
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
