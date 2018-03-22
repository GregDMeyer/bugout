'''
This file is part of BUGOUT
(c) Greg Meyer, 2018
'''

from time import sleep
from sys import stdout, stderr
from fortranformat import FortranRecordReader
from os import path
from functools import partial
import numpy as np
from os.path import isdir, isfile
from os import listdir
from string import ascii_letters, digits, punctuation
valid_chars = ascii_letters + digits + punctuation

DEBUG = True

### INTERFACE

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

def parse_dirs_raw(dirs):
    '''
    Generate raw CSV files from the BUGIN files
    '''
    for directory in dirs:
        parse_and_write(directory)

def parse_dirs_combined(dirs):
    '''
    Generated clean CSV files combining the data.
    '''
    for directory in dirs:
        combine(directory)

def gen_master_samples(dirs, outfname):
    '''
    Generate a master samples CSV combining the sample lists in all of dirs,
    and write it to outfname.
    '''

    with open(outfname, 'w') as fout:

        first = True
        for d in dirs:
            if not isfile(path.join(d,'clean_samples.csv')):
                # need to generate it
                success = combine(d, do_abund=False)

                if not success:
                    continue

            with open(path.join(d,'clean_samples.csv')) as fin:
                # skip the headers on all but the first one
                if not first:
                    fin.readline()
                else:
                    first = False

                fout.write(fin.read())

def combine(directory, do_abund=True):
    '''
    Read in SAMPLES, SPECIES, ABUNDAN, and HEADER, and collect them into one file.
    '''

    if DEBUG:
        print('Processing %s' % directory)

    required = ['SAMPLES', 'HEADER']
    if do_abund:
        required += ['SPECIES', 'ABUNDAN']
    optional = ['SAMPLE2']
    present = listdir(directory)

    if not all(f in present for f in required):
        print('Warning: Could not find necessary files in directory "%s". '
              'Skipping...' % directory)
        return False

    data = {}
    for fname in required + [f for f in optional if f in present]:
        data[fname], _ = read_bugin(directory, fname)

    file_fields = ['Name']
    abund_fields = ['Frequency']
    species_fields = ['Taxa']
    sample_fields = [k for k,_ in data['SAMPLES'][0]]
    header_fields = [k for k,_ in data['HEADER'][0]]
    if 'SAMPLE2' in data:
        sample2_fields = [k for k,_ in data['SAMPLE2'][0]]
    else:
        fields = convert_fields(binary_types['SAMPLE2'])['field_names']
        sample2_fields = [field for field in fields if field != '']

    file_data = {'Name' : directory.rstrip('/').split('/')[-1]}

    if do_abund:
        # write filled-out abundance file
        with open(path.join(directory, 'clean_abundance.csv'), 'w') as f:

            # write out header
            f.write(','.join(file_fields + abund_fields + species_fields +\
                             sample_fields + sample2_fields + header_fields))
            f.write('\n')

            for n,d in enumerate(data['ABUNDAN'][1:]):
                vals = []

                vals += [file_data[k] for k in file_fields]

                abund = dict(d)
                vals += [abund[k] for k in abund_fields]

                spec_idx = abund['Pointer to SPECIES File']
                try:
                    spec = dict(data['SPECIES'][spec_idx])
                except IndexError:
                    if DEBUG:
                        print('Index %d out of bounds for SPECIES file.' % spec_idx)
                    spec = {k : '' for k in species_fields}

                vals += [spec[k] for k in species_fields]

                # TODO: can use a better data structure for speed, if we decide we need it
                sample_idx = abund['Pointer to SAMPLES File']
                try:
                    sample = dict(data['SAMPLES'][sample_idx])
                except IndexError:
                    if DEBUG:
                        print('Index %d out of bounds for SAMPLES file.' % sample_idx)
                    sample = {k : '' for k in sample_fields}

                sample2_idx = abund['Pointer to SAMPLES File']-1
                if 'SAMPLE2' in data:
                    if sample2_idx < len(data['SAMPLE2']):
                        sample.update(dict(data['SAMPLE2'][sample2_idx]))
                    else:
                        print('Index %d out of bounds for SAMPLE2 file.' % sample2_idx)
                        for k in sample2_fields:
                            sample[k] = '[Missing data! Previous rows for this well ' +\
                                        'may be out of place...]'
                else:
                    for k in sample2_fields:
                        sample[k] = ''

                # make sure we actually read the right one
                assert(sample['Sample Index'] == abund['Pointer to SAMPLES File'])

                vals += [sample[k] for k in sample_fields + sample2_fields]

                # write out the header stuff on the first row
                if n == 0:
                    header = dict(data['HEADER'][0])
                    vals += [header[k] for k in header_fields]

                str_vals = [str(v) for v in vals]
                str_vals = [v.join('""') if ',' in v else v for v in str_vals]

                f.write(','.join(str_vals))
                f.write('\n')

    # write filled-out samples file
    with open(path.join(directory, 'clean_samples.csv'), 'w') as f:

        # write out header
        f.write(','.join(file_fields + sample_fields + sample2_fields + header_fields))
        f.write('\n')

        for n,d in enumerate(data['SAMPLES'][1:]):
            vals = []

            vals += [file_data[k] for k in file_fields]

            sample = dict(d)

            if 'SAMPLE2' in data and len(data['SAMPLE2']) > n:
                d2 = data['SAMPLE2'][n]
                sample.update(dict(d2))
            else:
                if 'SAMPLE2' not in data:
                    s = ''
                else:
                    s = '[Missing data! Previous rows for this well ' +\
                        'may be out of place...]'

                for k in sample2_fields:
                    sample[k] = s

            vals += [sample[k] for k in sample_fields + sample2_fields]

            # write out the header stuff
            header = dict(data['HEADER'][0])
            vals += [header[k] for k in header_fields]

            str_vals = [str(v).replace('"','') for v in vals]
            str_vals = [v.join('""') if ',' in v else v for v in str_vals]

            f.write(','.join(str_vals))
            f.write('\n')

    return True

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

        if DEBUG:
            print('Processing file %s' % path.join(directory, ftype))

        data, extra_data = read_bugin(directory, ftype)

        with open(path.join(directory,ftype+'.csv'), 'w') as f:

            if len(data) == 0:
                continue

            f.write(','.join(k for k,_ in data[0]))
            f.write('\n')

            for d in data:
                s = ''
                for _,v in d:
                    ss = str(v)
                    if ',' in ss:
                        ss = '"%s"' % ss
                    s += ss + ','
                f.write(s)
                f.write('\n')

    return

### FILE READING

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
    contents = []
    field_names = [n for n in field_names if n]

    reader = FortranRecordReader(format_spec)

    with open(filename, 'r') as f:
        # get through the initial header part
        # TODO: assert this has the right format
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
        #f.seek(record_length)
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
            val = int.from_bytes(cur, 'little')

        elif fmt['type'] == 'X':
            if DEBUG and cur != b' ':
                pass
                #print('Threw away bytes at format index %d:\n%s' % (n, cur))
            continue

        elif fmt['type'] == 'F':
            try:
                val = float(cur)
            except:
                val = -1

        rtn.append((name,val))

    if DEBUG and b:
        pass
        #print('Remaining bytes:%s\n' % b)

    return rtn

def convert_fields(d):

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
