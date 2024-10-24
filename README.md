# BUGOUT

The purpose of this software is to read in paleontological data that was recorded using BUGIN, an old piece of software for MS-DOS, and convert it to CSV.
Much of this code was reverse-engineered from BUGIN output files; if you find a problem or it doesn't work perfectly, please [submit an issue](https://github.com/GregDMeyer/bugout/issues).
If you would like to read the story of how this script came to be, see my blog post [here](https://gregkm.me/blog/posts/bugout/).

## Usage

With Python 3 installed, BUGOUT can simply be run as `./BUGOUT <directories>`, or `python3 BUGOUT <directories>`, where `<directories>` is a list of one or more directories containing BUGIN output
BUGOUT can accumulate the data from multiple directories into one master CSV file, with the `-m <master file>` command-line option.
By default BUGOUT combines the data from BUGIN's `SAMPLES`, `SPECIES`, etc. files into one spreadsheet; these files can instead be converted to individual CSVs with the `--raw` flag.

Here are the full command line options:

```
usage: BUGOUT [-h] [-m FILE] [--raw] [--retro] [directories ...]

positional arguments:
  directories           The directories to be processed.

options:
  -h, --help            show this help message and exit
  -m FILE, --master_samples_file FILE
                        File in which to accumulate all samples.
  --raw                 Generate raw CSVs of BUGIN files, instead of clean combined files.
  --retro               Find some illusion of joy in a fallen world.
```
