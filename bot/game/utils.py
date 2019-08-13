from pyfiglet import figlet_format
from termcolor import cprint


def draw_banner(text: str, font: str = None, color: str = None, bold: bool = False):
    font = font or 'standard'
    color = color or 'cyan'
    attrs = []

    if bold:
        attrs.append('bold')

    ascii_text = figlet_format(text, font)
    cprint(ascii_text, color, attrs=attrs)
