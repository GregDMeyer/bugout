
from time import sleep
from sys import stdout, stderr
from fortranformat import FortranRecordReader
from os import path
from functools import partial
import numpy as np
from os.path import isdir
from os import listdir
from string import ascii_letters, digits, punctuation
valid_chars = ascii_letters + digits + punctuation

### INTERFACE

def retro():
    '''
    Find some illusion of joy in a fallen world
    '''

    slow_output('''
    WELCOME TO BUGOUT V 0.0.1

    WRITTEN BY GREG MEYER, 2018

    ''')

    slow_output('''PLEASE INPUT DIRECTORY NAME: ''')
    directory = input()
    while not isdir(directory):
        slow_output('''INVALID DIRECTORY. TRY AGAIN: ''')
        directory = input()

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

def parse_dirs(dirs):
    '''
    The boring, actually useful way
    '''
    for directory in dirs:
        parse_and_write(directory)

def parse_and_write(directory):
    '''
    Parse all bugin files in the directory, and write them in CSV
    format to the same.
    '''

    file_types = list(binary_types) + \
                 list(ascii_types) + \
                 list(user_types)

    files = listdir(directory)

    valid_files = [f for f in files if f in file_types]

    if not valid_files:
        print('Warning: no BUGIN files found in directory "%s"' % directory)
        return

    for ftype in valid_files:
        data, extra_data = read_bugin(directory, ftype)
        if data is None:
            print(ftype)

        with open(path.join(directory,ftype+'.csv'), 'w') as f:

            f.write(','.join(k for k,_ in data[0]))
            f.write('\n')

            for d in data:
                f.write(','.join(str(v) for _,v in d))
                f.write('\n')

    return

### FILE READING

def read_user_file(filename, field_names, format_spec, record_length):
    contents = []
    field_names = [n for n in field_names if n]

    reader = FortranRecordReader(format_spec)

    with open(filename, 'r') as f:
        # get through the initial header part
        f.readline()
        qualifiers = []
        for line in f:
            if line.startswith(' '*10):
                # it's the category qualifier things
                qualifiers.append(line.strip())
            else:
                vals = reader.read(line)
                contents.append(list(zip(field_names, vals)))

    return contents, qualifiers

def read_ascii_file(filename, field_names):
    with open(filename) as f:
        rtn = [[]]
        n_fields = len(field_names)
        lines = f.readlines()
        for field, value in zip(field_names,
                                lines[:n_fields]):
            rtn[0].append((field, value.strip()))

        rtn[0][-1] = (rtn[0][-1][0],
                      rtn[0][-1][1] + ' '.join(l.strip() for l in lines[n_fields:]))
    return rtn

def read_binary_file(filename, field_names, format_spec, record_length):
    '''
    Read a BUGIN file unformatted binary format.

    Parameters
    ----------
    filename : str
        The file path

    field_names : list
        A list of the names for the corresponding fields in format_spec.

    format_spec : str
        A FORTRAN format string.

    record_length : int
        The number of bytes in a record.
    '''

    contents = []

    with open(filename, 'rb') as f:
        f.seek(record_length)
        for chunk in iter(partial(f.read, record_length), ''):
            if not chunk:
                break
            contents.append(bytes_to_list(chunk, format_spec, field_names))

    return contents

def parse_format_string(s):
    s = s.strip('()')
    vals = s.split(', ')
    rtn = []
    for v in vals:
        try:
            count = int(v[0])
            v = v[1:]
        except ValueError:
            count = 1

        d = {}
        d['type'] = v[0]
        if len(v) == 1:
            d['size'] = 1
        else:
            d['size'] = int(v[1:].split('.')[0])

        rtn += [d]*count

    return rtn

def bytes_to_list(b, format_spec, field_names):

    formats = parse_format_string(format_spec)

    rtn = []
    for fmt, name in zip(formats, field_names):
        cur = b[:fmt['size']]
        b = b[fmt['size']:]

        if fmt['type'] == 'A':
            val = cur.decode('ASCII')
        elif fmt['type'] == 'I':
            val = int.from_bytes(cur, 'big')
        elif fmt['type'] == 'X':
            continue
        elif fmt['type'] == 'F':
            try:
                val = float(cur)
            except:
                val = -1

        rtn.append((name,val))

    return rtn

def read_bugin(directory, file_type):
    '''
    Actually read in bugin files!

    Parameters
    ----------

    directory : str
        The directory to read from

    file_type : str
        Which file to read. Options are SAMPLE, SPECIES, ABUNDAN,
        USER, SPSADD, HEADER.
    '''

    if file_type in binary_types:
        extra_data = None
        rtn = read_binary_file(path.join(directory, file_type),
                               **binary_types[file_type])

    elif file_type in ascii_types:
        extra_data = None
        rtn = read_ascii_file(path.join(directory, file_type),
                              **ascii_types[file_type])

    elif file_type in user_types:
        rtn, extra_data = read_user_file(path.join(directory, file_type),
                                         **binary_types['SPECIES'])

    else:
        raise ValueError('Unrecognized file type %s' % file_type)

    return rtn, extra_data

binary_types = {
    'SAMPLES' : {
        'record_length' : 200,
        'format_spec' : '(2F8.2, I4, A40, A4, A25, A5, A5, A4, A32, A6, A50, A1)',
        'field_names' : [
            'Sample Top',
            'Sample Bottom',
            'Sample Index',
            'Sample Comment',
            'Lithology Code',
            'Lithology Data',
            'Bathymetry Top',
            'Bathymetry Bottom',
            'Depositional Environment Code',
            'Depositional Environment Data',
            'Age Code',
            'Zone Information',
            'Stratigraphic Break'
        ]
    },
    'SPECIES' : {
        'record_length' : 65,
        'format_spec' : '(A7, 1X, A50, A2, A1)',
        'field_names' : [
            'Species Code',
            '',
            'Taxa',
            'Qualifier',
            'Active/Not Active Flag'
        ]
    },
    'ABUNDAN' : {
        'record_length' : 15,
        'format_spec' : '(A5, 1X, I3, 1X, A1, I4)',
        'field_names' : [
            'Frequency',
            '',
            'Pointer to SPECIES File',
            '',
            'Marker or Rework Flag',
            'Pointer to SAMPLES File'
        ]
    }
}

ascii_types = {
    'HEADER' : {
        'field_names' : [
            'Operator',
            'API no.',
            'Well Name/Block no.',
            'Well no.',
            'Survey Name/Abstract',
            'S/T',
            'Field Name',
            'OCS no.',
            'County/Parish/Area',
            'Section',
            'Township',
            'Range',
            'State',
            'Onshore/Offshore',
            'State/Federal',
            'Bug Group Type',
            'Report (Sum/Detail)',
            'Well/Outcrop',
            'Confidential (y/n)',
            'KB Elevation',
            'Latitude',
            'Longitude',
            'Total Depth',
            'TVD',
            'Form. at TD',
            'Straight/Deviated',
            'Sample Range Top',
            'Sample Range Bottom',
            'Range Examined Top',
            'Range Examined Bottom',
            'Analyst',
            'Source Company',
            'Comments'
        ]
    },
}

user_types = {'USER', 'SPSADD'}
