from setuptools import setup, find_packages

version = '0.0.1.dev0'

setup(
    name='Energy Game',
    version=version,
    description='Bot for game.energy.ch',
    long_description=open('README.rst').read(),

    # Get more strings from
    # http://www.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
    ],

    keywords='nachtalb,energy.ch',
    author='Nachtalb',
    author_email='mailto:info@nachtalb.ch',
    url='https://github.com/Nachtalb/energy_game',
    license='THE BEER-WARE LICENSE',
    license_file='LICENSE.txt',

    packages=find_packages(),

    install_requires=[
        'PyInquirer==1.0.3',
        'pyfiglet==0.8.post1',
        'termcolor==1.1.0',
        'prompt-toolkit==1.0.14',
    ],
    entry_points={'console_scripts': ['energy=bot.game.cli:main']},
)
