'''
This file is part of BUGOUT
(c) Greg Meyer, 2018
'''

'''
Validate various data types.
'''

from os.path import isdir, isfile

def directories(dirs):
    rtn = []
    for d in dirs:
        if not isdir(d):
            raise ValueError('command line argument "%s" is not a directory.' % d)
        else:
            rtn.append(d)
    return rtn

def outfile(f):
    if isfile(f):
        print('Output file exists. Overwrite? (y/n): ',end='')
        if input() != 'y':
            print('Exiting...')
            exit()

    elif isdir(f):
        raise ValueError('Output file is a directory! Did you forget to pass '
                         'a filename to the -m argument?')

    return f
