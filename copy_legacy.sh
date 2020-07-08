#!/bin/bash
#
# copy_legacy.sh - Copy GLAST data from NASA "legacy" machine using ftpsync.py
# Stephen Fegan - sfegan@llr.in2p3.fr - 2009-11-14
# $Id$
#

BASEDIR=/sps/hep/glast/data/FSSCWeeklyData
FTPBASE=ftp://legacy.gsfc.nasa.gov/fermi/data/lat/weekly
FT1DIR=legacy.gsfc.nasa.gov/photon_p8_v302
FT2DIR=legacy.gsfc.nasa.gov/spacecraft
cd ${BASEDIR} 

# Copy over data from legacy - FT1 and FT2
echo Copying data from... 
ftpsync.pl $FTPBASE/photon ${FT1DIR}
ftpsync.pl $FTPBASE/spacecraft ${FT2DIR}

# Merge FT2 data and sort
echo Merging and sorting FT2 data...
echo ${BASEDIR}/${FT2DIR}/*.fits | xargs -n1 echo > FT2.dat
ftmerge @FT2.dat \!FT2uo.fits
ftsort FT2uo.fits \!FT2.fits START
rm -f FT2uo.fits

# Make RAW FT1 list
echo ${BASEDIR}/${FT1DIR}/*.fits | xargs -n1 echo > FT1_P8_SOURCE.dat

# Run Sun/Moon script
echo Calculating Sun and Moon positions...
sunmoon_ft2.py FT2.fits > sunmoon.dat
