
from time import sleep
from sys import stdout
from fortranformat import FortranRecordReader
from os import path
from functools import partial
import numpy as np

def slow_output(s):
    '''
    Find some illusion of joy in a fallen world
    '''
    for c in s:
        print(c,end='')
        stdout.flush()
        if c != ' ':
            sleep(0.02)

def read_ascii_file(filename, field_names, format_spec, record_length):
    # contents = []
    #
    # with open(filename, 'rb') as f:
    #     for chunk in iter(partial(f.read, record_length), ''):
    #         if not chunk:
    #             break
    #         contents.append(bytes_to_dict(chunk, format_spec, field_names))
    #
    # return contents
    pass

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
        for chunk in iter(partial(f.read, record_length), ''):
            if not chunk:
                break
            contents.append(bytes_to_dict(chunk, format_spec, field_names))

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

def bytes_to_dict(b, format_spec, field_names):

    formats = parse_format_string(format_spec)

    rtn = {}
    for fmt, name in zip(formats, field_names):
        cur = b[:fmt['size']]
        b = b[fmt['size']:]

        if fmt['type'] == 'A':
            val = cur.decode('ASCII')
        elif fmt['type'] == 'I':
            val = int.from_bytes(cur, 'little')
        elif fmt['type'] == 'X':
            continue
        elif fmt['type'] == 'F':
            val = np.frombuffer(cur)

        rtn[name] = val

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
        rtn = read_binary_file(path.join(directory, file_type),
                               **binary_types[file_type])

    elif file_type in ascii_types:
        with open(path.join(directory,file_type)) as f:
            rtn = [{}]
            n_fields = len(ascii_types[file_type]['field_names'])
            lines = f.readlines()
            for field, value in zip(ascii_types[file_type]['field_names'],
                                    lines[:n_fields]):
                rtn[0][field] = value.strip()

            rtn[0]['Comments'] += ' '.join(l.strip() for l in lines[n_fields:])

    elif file_type in user_types:
        rtn = read_ascii_file(path.join(directory, file_type),
                              **binary_types['SPECIES'])

    else:
        raise ValueError('Unrecognized file type %s' % file_type)

    return rtn

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
