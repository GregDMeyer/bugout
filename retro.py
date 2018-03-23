'''
This file is part of BUGOUT
(c) Greg Meyer, 2018
'''

from sys import stdout
from time import sleep
from os.path import isdir
from os import listdir
from string import ascii_letters, digits, punctuation
valid_chars = ascii_letters + digits + punctuation

from file_write import combine, parse_and_write
from file_read import read_bugin, binary_types, user_types, ascii_types

DEBUG = True

def retro():
    '''
    Find some illusion of joy in a fallen world
    '''

    slow_output('''
    WELCOME TO BUGOUT V 0.0.1

    WRITTEN BY GREG MEYER, 2018

    ''')

    sleep(1)

    slow_output('''PLEASE INPUT DIRECTORY NAME: ''')
    directory = input().strip()
    while not isdir(directory):
        slow_output('''INVALID DIRECTORY. TRY AGAIN: ''')
        directory = input().strip()

    file_types = list(binary_types) + \
                 list(ascii_types) + \
                 list(user_types)
    file_types.sort()

    files = listdir(directory)
    valid_files = [f for f in files if f in file_types]
    valid_files.sort()

    if not valid_files:
        slow_output('''NO BUGIN OUTPUT FILES FOUND IN DIRECTORY. EXITING...''')
        exit()

    slow_output('''\nCHOOSE A FILE:\n\n''')

    for n,f in enumerate(valid_files):
        slow_output('  %d. %s\n' % (n+1, f))

    slow_output('\nSTRIKE A NUMBER KEY AND THEN DEPRESS <ENTER>: ')
    try:
        choice = int(input())-1
    except ValueError:
        choice = -1
    while choice not in range(len(valid_files)):
        slow_output('INPUT MUST BE A NUMBER BETWEEN 1 AND %d: ' % len(valid_files))
        try:
            choice = int(input())-1
        except ValueError:
            choice = -1

    file_type = valid_files[choice]

    result, extra_data = read_bugin(directory, file_type)

    for n,r in enumerate(result):
        slow_output('''\n\nRECORD %d/%d\n''' % (n+1,len(result)))
        maxlen = max(len(k) for k,_ in r)
        for k,v in r:
            slow_output(('    %-'+str(maxlen+1)+'s: %s\n') % (k.upper(), str(v)))

    slow_output('\n\n')

    slow_output('THANK YOU FOR USING BUGOUT. GOODBYE.\n\n')

def slow_output(s):
    '''
    Feel even more like you're playing Fallout
    '''
    for c in s:
        print(c,end='')
        stdout.flush()
        if c in valid_chars:
            sleep(0.015)
