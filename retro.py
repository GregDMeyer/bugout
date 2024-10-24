'''
This file is part of BUGOUT
(c) Greg Meyer, 2018
'''

from sys import stdout
from time import sleep
from os.path import isdir
from os import listdir, system, get_terminal_size
from string import ascii_letters, digits, punctuation
valid_chars = ascii_letters + digits + punctuation

from file_write import combine, parse_and_write
from file_read import read_bugin, binary_types, user_types, ascii_types

DEBUG = True

def retro():
    '''
    Find some illusion of joy in a fallen world
    '''

    printer = SlowPagePrinter()

    # clear the terminal
    system('clear')
    sleep(5)

    printer.print('''
    WELCOME TO BUGOUT V 0.0.1

    WRITTEN BY GREG MEYER, 2018

    ''')

    sleep(1)

    printer.print('''PLEASE INPUT DIRECTORY NAME: ''')
    directory = input().strip()
    printer.row += 1
    while not isdir(directory):
        printer.print('''INVALID DIRECTORY. TRY AGAIN: ''')
        directory = input().strip()
        printer.row += 1

    file_types = list(binary_types) + \
                 list(ascii_types) + \
                 list(user_types)
    file_types.sort()

    files = listdir(directory)
    valid_files = [f for f in files if f in file_types]
    valid_files.sort()

    if not valid_files:
        printer.print('''NO BUGIN OUTPUT FILES FOUND IN DIRECTORY. EXITING...''')
        exit()

    printer.print('''\nCHOOSE A FILE:\n\n''')

    for n,f in enumerate(valid_files):
        printer.print('  %d. %s\n' % (n+1, f))

    printer.print('\nSTRIKE A NUMBER KEY AND THEN DEPRESS <ENTER>: ')
    try:
        choice = int(input())-1
        printer.row += 1
    except ValueError:
        choice = -1
    while choice not in range(len(valid_files)):
        printer.print('INPUT MUST BE A NUMBER BETWEEN 1 AND %d: ' % len(valid_files))
        try:
            choice = int(input())-1
            printer.row += 1
        except ValueError:
            choice = -1

    sleep(1)

    file_type = valid_files[choice]

    result, extra_data = read_bugin(directory, file_type)

    for n,r in enumerate(result):
        printer.print('''\n\nRECORD %d/%d\n''' % (n+1,len(result)))
        maxlen = max(len(k) for k,_ in r)
        data_printed = False
        for k,v in r:
            if not v:
                continue
            printer.print(('    %-'+str(maxlen+1)+'s: %s\n') % (k.upper(), str(v)))
            data_printed = True
        if not data_printed:
            printer.print('     <NO DATA FOUND>')

    printer.print('\n\n')

    printer.print('THANK YOU FOR USING BUGOUT. GOODBYE.\n\n')


class SlowPagePrinter:
    '''
    Feel even more like you're playing Fallout
    '''

    def __init__(self, delay=0.015):
        self.delay = delay
        self.row = 0
        self.col = 0

    def print(self, string):
        ncol, nrow = get_terminal_size()
        for c in string:
            if c == '\n':
                self.row += 1

                if self.row >= nrow:
                    system('clear')
                    self.row = 1

                self.col = 0

            if self.col >= ncol:
                continue

            print(c, end='')
            stdout.flush()
            if c in valid_chars:
                sleep(self.delay)

            self.col += 1
