'''
This file is part of BUGOUT
(c) Greg Meyer, 2018
'''

from os import path
from functools import partial
from fortranformat import FortranRecordReader

DEBUG = True

def read_bugin(directory, file_type):
    '''
    Actually read in bugin files!

    Parameters
    ----------

    directory : str
        The directory to read from

    file_type : str
        Which file to read. Options are the keys of the dictionaries containing
        the format definitions (at the bottom of this file).
    '''

    if file_type in binary_types:
        extra_data = None
        d = convert_fields(binary_types[file_type])
        rtn = read_binary_file(path.join(directory, file_type), **d)

    elif file_type in ascii_types:
        extra_data = None
        rtn = read_ascii_file(path.join(directory, file_type),
                              **ascii_types[file_type])

    elif file_type in user_types:
        d = convert_fields(binary_types['SPECIES'])
        rtn, extra_data = read_user_file(path.join(directory, file_type), **d)

    else:
        raise ValueError('Unrecognized file type %s' % file_type)

    return rtn, extra_data

def read_user_file(filename, field_names, format_spec, record_length):
    '''
    Read a BUGIN file of the same type as the USER file (formatted FORTRAN ASCII).

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
    '''
    Read a BUGIN file in ASCII format.

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
        #f.seek(record_length)
        for chunk in iter(partial(f.read, record_length), ''):
            if not chunk:
                break
            contents.append(bytes_to_list(chunk, format_spec, field_names))

    return contents

def parse_format_string(s):
    '''
    Take a Fortran-stype format string and turn it into a list of type chars
    and field lengths.
    '''
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
    '''
    Parse a byte string of binary data, formatted as ``format_spec``, and
    generate a list of field name-value pairs.

    Parameters
    ----------

    b : bytes
        A byte string containing the data.

    format_spec : str
        A Fortran-style data formatting string.

    field_names : list of str
        A list of names for the fields enumerated in format_spec.
    '''

    formats = parse_format_string(format_spec)

    rtn = []
    for n, (fmt, name) in enumerate(zip(formats, field_names)):
        cur = b[:fmt['size']]
        b = b[fmt['size']:]

        if fmt['type'] == 'A':
            try:
                val = cur.decode('ASCII').strip()
            except UnicodeDecodeError:
                val = ''
                print('Decode failed for field "%s". Value was %s' % (name,cur))

        elif fmt['type'] == 'I':
            # via trial-and-error, it looks like their machines were little-endian
            val = int.from_bytes(cur, 'little')

        elif fmt['type'] == 'X':
            if DEBUG and cur != b' ':
                pass
                # print('Threw away bytes at format index %d:\n%s' % (n, cur))
                #
                # It turns out that this "space" is sometimes filled with random
                # bytes or chunks of data from other fields. I think that they
                # didn't clear the memory they allocated, and sometimes just write
                # random stuff from memory to disk.
            continue

        elif fmt['type'] == 'F':
            # it turns out their "floating point" format is just an ASCII string
            # writing the floating point number out.
            try:
                val = float(cur)
            except:
                val = -1

        rtn.append((name,val))

    if DEBUG and b:
        pass
        # print('Remaining bytes:%s\n' % b)
        #
        # At first I was concerned when the total sum of the bytes specified in
        # the format specification was less than the "record length" that
        # they write to disk. But it turns out they just leave uninitialized
        # memory left over at the end of each block, and write it to disk anyway.
        # Gotta love the 80's.

    return rtn

def convert_fields(d):
    '''
    Convert a list of field name-data format pairs into a Fortran-style format
    string and a list of field names.
    '''

    rtn = {'field_names' : []}
    fields = []

    for k, f in d['fields']:
        rtn['field_names'].append(k)
        fields.append(f)

    rtn['format_spec'] = '(%s)' % ', '.join(fields)
    rtn['record_length'] = d['record_length']

    return rtn

### DEFINITIONS OF FILE FORMATS

binary_types = {
    'SAMPLES' : {
        'record_length' : 200,
        'fields' : [
            ('Sample Top',      'F8.2'),
            ('Sample Bottom',   'F8.2'),
            ('Sample Index',    'I2'),
            ('Sample Comment',  'A40'),
            ('Lithology Code',  'A4'),
            ('Lithology Data',  'A25'),
            ('Bathymetry Top',  'A5'),
            ('Bathymetry Bottom','A5'),
            ('Depositional Environment Code', 'A4'),
            ('Depositional Environment Data', 'A32'),
            ('Age Code',        'A6'),
            ('Zone Code',       'A6'),
            ('Zone Information','A44'),
            ('Stratigraphic Break','A8'),
        ],
    },
    'SAMPLE2' : {
        'record_length' : 1020,
        'fields' : [
            ('',                'X60'),
            ('Lithology',  'A240'),
            ('Bathymetry',      'A240'),
            ('Depositional Environment', 'A240'),
            ('Zone Information 2','A240'),
        ],
    },
    'SPECIES' : {
        'record_length' : 65,
        'fields' : [
            ('Species Code',    'A7'),
            ('Taxa',            'A50'),
            ('Qualifier',       'A2'),
            ('Active/Not Active','A1'),
        ],
    },
    'ABUNDAN' : {
        'record_length' : 15,
        'fields' : [
            ('Frequency',               'A5'),
            ('Pointer to SPECIES File', 'I2'),
            ('Marker or Rework Flag',   'A1'),
            ('Pointer to SAMPLES File', 'I7')
        ],
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
