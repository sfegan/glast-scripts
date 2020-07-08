#!/bin/bash
#
# run_all_diffuse_P7SOURCE_V6.sh - Run P7SOURCE_V6 IRFs
# Stephen Fegan - sfegan@llr.in2p3.fr - 2010-05-26
# $Id$
#

IRF=P7SOURCE_V6

export BASEDIR=/sps/hep/glast/data/P7.6_P120_BASE
export INDIR=AstroServer
export OUTDIR=${IRF}
export LOGDIR=log_diffrsp
export GTDIFFRSP=/afs/in2p3.fr/group/glast/ground/releases/redhat5-x86_64-64bit-gcc41/ScienceTools/ScienceTools-v9r23p1/bin/redhat5-x86_64-64bit-gcc41-Optimized/gtdiffrsp

#export CUSTOM_IRF_DIR=${BASEDIR}/IRF/${IRF}
#export CUSTOM_IRF_NAMES=${IRF}

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
    cmd="qdiffrsp_p7.sh $fin ${BASEDIR}/${OUTDIR} ${IRF} ${GTDIFFRSP}"
    echo $cmd
    ( cd ${BASEDIR}/${LOGDIR}; $cmd )
  fi
done

