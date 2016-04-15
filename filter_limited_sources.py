#!/usr/bin/env python

# filter_limited_sources - remove sources at limits of spectrum
# Stephen Fegan - sfegan@llr.in2p3.fr - 2009-02-03
# $Id: filter_limited_sources.py 2003 2010-07-28 10:48:28Z sfegan $

from ModelManipulator import *
import sys

if len(sys.argv) < 2:
    print "usage: %s model_file_in [model_file_out] [ra dec inner_radius]"%sys.argv[0]
    sys.exit(0)

m = ModelManipulator(sys.argv[1])

if len(sys.argv)>5:
    ra = float(sys.argv[3])
    dec = float(sys.argv[4])
    radius = float(sys.argv[5])
    base = m.listROISources(ra, dec, 180.0, radius);
else: 
    base = m.listPointSources();
   
for node in m.listSourcesAtSpectrumLimits(base):
    print "Deleting: ", m.sourceName(node)

if len(sys.argv) > 2:
    m.output(sys.argv[2])
else:
    m.output()
