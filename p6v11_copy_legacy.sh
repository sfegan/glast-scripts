#!/bin/bash
#
# copy_legacy.sh - Copy GLAST data from NASA legacy machine using ftpsync.py
# Stephen Fegan - sfegan@llr.in2p3.fr - 2009-11-14
# $Id: copy_legacy.sh 2481 2011-01-21 11:06:36Z sfegan $
#

BASEDIR=/sps/hep/glast/data/FSSCWeeklyData
FT1DIR=legacy.gsfc.nasa.gov/photon_p6v3
FT2DIR=legacy.gsfc.nasa.gov/spacecraft
DIFDIR=legacy.gsfc.nasa.gov/P6_V3_DIFFUSE
cd ${BASEDIR} 

# Copy over data from legacy - FT1 and FT2
# ftpsync.pl -v ignoremask=_v01_Diffuse.fits ftp://legacy.gsfc.nasa.gov/glast/data/lat/weekly/photon ${FT1DIR}
# ftpsync.pl -v ignoremask=_v01_Diffuse.fits ftp://legacy.gsfc.nasa.gov/glast/data/lat/weekly/spacecraft ${FT2DIR}
ftpsync.pl -v ignoremask=LAT_allsky_ ftp://legacy.gsfc.nasa.gov/glast/data/lat/weekly/p6v11/photon ${FT1DIR}
ftpsync.pl -v ignoremask=_W_V01.fits ftp://legacy.gsfc.nasa.gov/glast/data/lat/weekly/p6v11/spacecraft ${FT2DIR}

# Merge FT2 data and sort
echo ${BASEDIR}/${FT2DIR}/*.fits | xargs -n1 echo > FT2.dat
ftmerge @FT2.dat \!FT2uo.fits
ftsort FT2uo.fits \!FT2.fits START
rm -f FT2uo.fits

# Make RAW FT1 list
echo ${BASEDIR}/${FT1DIR}/*.fits | xargs -n1 echo > FT1_SOURCE.dat

# Make DIFFUSE FT1 list
cd ${DIFDIR}
for f in ${BASEDIR}/${FT1DIR}/*.fits
do 
  md5=`md5sum $f | cut -d\\  -f1`
  of=`basename $f .fits`_$md5.fits;
  if /usr/bin/test \! -f $of; 
  then 
    rm -f `basename $f .fits`_*.fits
    ftcopy $f'[EVENT_CLASS>=3&&ZENITH_ANGLE<=110]' `basename $f .fits`_$md5.fits
  fi
  echo `/bin/pwd`/$of
done | tee ${BASEDIR}/FT1_P6_V3_DIFFUSE.dat

