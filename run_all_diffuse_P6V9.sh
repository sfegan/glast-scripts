#!/bin/bash
#
# run_all_diffuse.sh - Run P6V8 IRFs
# Stephen Fegan - sfegan@llr.in2p3.fr - 2010-05-26
# $Id: run_all_diffuse.sh 1870 2010-06-07 11:30:42Z sfegan $
#

IRF=P6_V9_DIFFUSE

BASEDIR=/sps/hep/glast/users/sfegan/newdata
INDIR=legacy.gsfc.nasa.gov/P6_V3_DIFFUSE
OUTDIR=legacy.gsfc.nasa.gov/${IRF}
LOGDIR=legacy.gsfc.nasa.gov/log_diffrsp
GTDIFFRSP=${BASEDIR}/ScienceTools-v9r16p1/bin/gtdiffrsp

# Delete unwanted files
cd ${BASEDIR}/${OUTDIR}
for f in *.fits
do
  fin=${BASEDIR}/${INDIR}/$f
  if /usr/bin/test \! -f "$fin";
  then
    echo rm -f $f
    rm -f $f
  fi
done

# Make RAW FT1 list
cd ${BASEDIR} 
echo ${BASEDIR}/${OUTDIR}/*.fits | xargs -n1 echo > FT1_${IRF}.dat
 
# Run qdiffrsp on missing files
cd ${BASEDIR}/${INDIR}
for f in *.fits
do
  fin=${BASEDIR}/${INDIR}/$f
  fout=${BASEDIR}/${OUTDIR}/$f
  if /usr/bin/test \! -f $fout;
  then
    cmd="qdiffrsp.sh $fin ${BASEDIR}/${OUTDIR} ${IRF} ${GTDIFFRSP}"
    echo $cmd
    ( cd ${BASEDIR}/${LOGDIR}; $cmd )
  fi
done

