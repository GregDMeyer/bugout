'''
This file is part of BUGOUT
(c) Greg Meyer, 2018
'''

from os import listdir, path
from file_read import read_bugin, convert_fields
from file_read import binary_types, ascii_types, user_types

DEBUG = False

def combine(directory, do_abund=True):
    '''
    Read in SAMPLES, SAMPLE2, SPECIES, ABUNDAN, and HEADER, and generate the
    combined output files "clean_abundance.csv" and "clean_samples.csv".

    Parameters
    ----------

    directory : str
        The directory in which to look for the files.

    do_abund : bool
        If set to false, "abundance.csv" will not be created

    Returns
    -------

    bool
        Whether the files were successfully generated (i.e. whether all
        necessary input files could be found).
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

    file_fields = ['Name', 'Source directory']
    abund_fields = ['Frequency']
    species_fields = ['Taxa']
    sample_fields = [k for k,_ in data['SAMPLES'][0]]
    header_fields = [k for k,_ in data['HEADER'][0]]
    if 'SAMPLE2' in data:
        sample2_fields = [k for k,_ in data['SAMPLE2'][0]]
    else:
        fields = convert_fields(binary_types['SAMPLE2'])['field_names']
        sample2_fields = [field for field in fields if field != '']

    file_data = {
        'Source directory' : directory,
        'Name' : directory.rstrip('/').split('/')[-1]
    }

    if do_abund:
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
                        # TODO: I think SAMPLE2 is aligned somehow with SAMPLES
                        # in a way I don't know
                        # print('Index %d out of bounds for SAMPLE2 file.' % sample2_idx)
                        for k in sample2_fields:
                            sample[k] = '--'
                else:
                    for k in sample2_fields:
                        sample[k] = ''

                # make sure we actually read the right one
                if sample['Sample Index'] != abund['Pointer to SAMPLES File'] and DEBUG:
                    print('Sample index incorrect')

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
                    s = '--'

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
                # write out the data string, making sure that we put quotes around
                # commas!
                # TODO: use csv.writer
                s = ''
                for _,v in d:
                    ss = str(v).replace('"','')
                    if ',' in ss:
                        ss = '"%s"' % ss
                    s += ss + ','
                f.write(s)
                f.write('\n')

    return

def gen_master_samples(dirs, outfname):
    '''
    Generate a master samples CSV combining the sample lists in all of dirs,
    and write it to outfname.
    '''

    with open(outfname, 'w') as fout:

        first = True
        for d in dirs:
            if not path.isfile(path.join(d,'clean_samples.csv')):
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
