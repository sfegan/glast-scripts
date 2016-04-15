#!/usr/bin/env python

# freeze_spectra - freeze spectral parameters in a model file
# Stephen Fegan - sfegan@llr.in2p3.fr - 2009-02-11
# $Id: freeze_spectra.py 2003 2010-07-28 10:48:28Z sfegan $

from ModelManipulator import *
import sys, getopt

def usage(progname):
    progparts = progname.split('/')
    print """usage: %s [-h] [-v] [-r] [-o out_file] in_file [source_name...]

Freeze spectral parameters from a model file.

infile:      name of XML model file to read

source_name: list of source names to freeze. If none is given then all sources
             are frozen. If the '-r' option is given, source names can be
             regular expressions, such as 'ASO.*' to freeze all names begining
             with ASO. Otherwise exact names, such as 'PKS_2155-304' will be
             matched.

-h:          print this message

-r:          match names using regular expressions

-v:          invert sense of matching (i.e. only freeze sources NOT in the
             given list)

-o out_file: name of XML file to write. Model is written to standard output if
             this option is not given"""%progparts[-1]
    sys.exit(0)
    
try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], 'hrvo:')
except getopt.GetoptError, err:
    # print help information and exit:
    print str(err) # will print something like "option -a not recognized"
    usage(sys.argv[0])

output = ""
noregex = True
invert = False

for o, a in opts:
    if o in ("-h"):
        usage(sys.argv[0])
    elif o in ("-o"):
        output = a
    elif o in ("-r"):
        noregex = False
    elif o in ("-v"):
        invert = True

if len(args) < 1:
    usage(sys.argv[0])

m = ModelManipulator(args[0])

if len(args) > 1:
    names = sys.argv[1:]
    sources = m.listNamedSources(names, noregex=noregex)
    if invert:
        sources = m.listUnlistedSources(sources)
else:
    sources = m.listAllSources()

for node in sources:
#    print m.sourceName(node)
    m.sourceFreezeParametersByName(node)

if output:
    m.output(output)
else:
    m.output()
