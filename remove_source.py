#!/usr/local/bin/python

# remove_source.py - remove a source from a model XML file
# Stephen Fegan - sfegan@llr.in2p3.fr - 2008-10-24
# $Id: remove_source.py 2003 2010-07-28 10:48:28Z sfegan $

import sys, xml.dom.minidom, getopt, os, time, re

def usage():
    print '''Usage: %s [OPTIONS] model_file source_name [source_name...]

Options:
  -h, --help     Print this message
  -o, --output   Output filename
  -n, --noregex  Disable regular expression matching

Remove one or more sources from a source library file. The sources are
matched by name, and do not necessaily have to be point source
entries. A regular expression can also be given, unless the "-n"
option is used. For example:

$ %s august_catalog.xml AUG0002_v1 AUG.\*v2

would remove the entries for "AUG0002_v1" and all those starting with
"AUG" and ending with "v2"\
'''%(sys.argv[0],sys.argv[0])

output = None
noregex = False

try:
    optspec = ( "help", "output=", "noregex" )
    opts, args = getopt.gnu_getopt(sys.argv[1:], 'ho:n', optspec)
except getopt.GetoptError, err:
    print str(err)
    usage()
    sys.exit(2)

for o, a in opts:
    if o in ("-h", "--help"):
        usage()
        sys.exit()
    elif o in ("-o", "--output"):
        output = a
    elif o in ("-n", "--noregex"):
        noregex = True
    else:
        assert False, "unhandled option"

if len(sys.argv) < 3:
    usage()
    sys.exit(1)

doc = xml.dom.minidom.parse(sys.argv[1])

delete_list = sys.argv[2:]

for source in doc.getElementsByTagName('source'):
    name = source.getAttribute('name')
    deleteme = False
    if  noregex:
        if name in delete_list:
            deleteme = True
    else:
        for delete_name in delete_list:
            if re.match(delete_name+'$', name):
                deleteme = True
                break

    if deleteme:
        source.parentNode.insertBefore(doc.createComment(\
              'Source %s removed by %s for %s at %s'%(name,os.getlogin(),\
                                     sys.argv[0],time.asctime())),source)
        source.parentNode.removeChild(source)

if output:
    open(output,'w').write(doc.toxml())
else:
    print doc.toxml(),
