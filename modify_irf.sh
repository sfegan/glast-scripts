#!/bin/bash

# modify_irfs.sh - copy and modify IRFs from the originals
# Stephen Fegan - sfegan@llr.in2p3.fr - 2011-03-31
# $Id: modify_irf.sh 2703 2011-03-31 11:31:08Z sfegan $

STDIR="$1"
ODIR="$2"
IRF="$3"
ENERGY="$4"

CALDB="data/caldb/data/glast/lat/bcf"

if test "$STDIR" == "" -o "$ODIR" == "" -o "$IRF" == "" -o "$ENERGY" == ""
then
  echo "usage: $0 ScienceToolsDirectory OutputDirectory IRFName Energy"
  exit
fi

if test \! -d $STDIR/$CALDB
then
  echo "CALDB directory \"$STDIR/$CALDB\" does not exist"
  exit
fi

if test \! -d $ODIR
then
  echo "Output directory \"$ODIR\" does not exist"
  exit
fi

# Copy original IRFs to output directory
cp $STDIR/$CALDB/psf/psf_${IRF}_*.fits $ODIR
cp $STDIR/$CALDB/edisp/edisp_${IRF}_*.fits $ODIR
cp $STDIR/$CALDB/ea/aeff_${IRF}_*.fits $ODIR

cd ${ODIR}

# Make copies of original PSF and EDISP IRFs under new names
for f in psf_${IRF}_*.fits edisp_${IRF}_*.fits
do
  if test \! -f $f
  then
    echo \"$f\" does not exist ... script failed
    exit
  fi
  echo Copying: $f
  for s in fluxlo fluxhi indexsoft indexhard
  do 
    cp $f ${f/$IRF/mod_$s}
  done
done

# Modify EA IRFs and save them under new names
for f in aeff_${IRF}_*.fits
do
  if test \! -f $f
  then
    echo \"$f\" does not exist ... script failed
    exit
  fi
  echo Modifying: $f
  for s in fluxlo fluxhi indexsoft indexhard
  do
    of=${f/$IRF/mod_$s}
    make_bracketing_ea.py $f $of $s $ENERGY > ${of/fits/dat}
  done
done
