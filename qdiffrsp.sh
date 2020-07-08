#!/bin/sh

# qdiffrsp.sh - Send a gtdiffrsp job to the batch queue @ ccin2p3
# Stephen Fegan - sfegan@llr.in2p3.fr - 2008-10-17
# $Id$

if test "$1" == ""
then
  echo "Usage: $0 ft1_file [outdir] [IRF]"
  exit
fi

irf=$3
if test "$irf" == ""
then
  irf=P6_V11_DIFFUSE
fi

basedir=/sps/hep/glast/data/FSSCWeeklyData
datadir=$basedir/legacy.gsfc.nasa.gov
diffdir=$basedir/diffuse

outdir=$2
if test "$outdir" == ""
then 
  outdir=${datadir}/${irf}
fi

gtdiffrsp=$4
if test "$gtdiffrsp" == ""
then
  gtdiffrsp=/afs/in2p3.fr/group/glast/ground/releases/rhel4_gcc34opt/ScienceTools/ScienceTools-v9r16p1/bin/gtdiffrsp
fi

# When making changes watch the use of $ and \$ in the automaticlly
# generated script given to qsub

#cat <<EOF
qsub <<EOF
#!/bin/bash
#PBS -l t=4286000,M=1024MB,platform=LINUX,scr=4096MB,u_sps_glast
#PBS -eo -V 
### -me -mu sfegan@llr.in2p3.fr
if test "$CUSTOM_IRF_NAMES" \!= ""
then
  export CUSTOM_IRF_NAMES=$CUSTOM_IRF_NAMES
  echo CUSTOM_IRF_NAMES=\$CUSTOM_IRF_NAMES
fi
if test "$CUSTOM_IRF_DIR" \!= ""
then
  export CUSTOM_IRF_DIR=$CUSTOM_IRF_DIR
  echo CUSTOM_IRF_DIR=\$CUSTOM_IRF_DIR
fi
. \$HOME/.bash_profile
PFILES=.:\$PFILES
cd \$TMPBATCH
pwd
echo $1
cp $1 .
if test -f ${diffdir}/diffuse_model_${irf}.xml
then
  cmd="cp ${diffdir}/diffuse_model_${irf}.xml diffuse_model.xml"
else
  cmd="cp ${diffdir}/diffuse_model.xml diffuse_model.xml"
fi
echo \$cmd
\$cmd
cp /sps/hep/glast/data/FSSCWeeklyData/FT2.fits .
ls -al
cmd="$gtdiffrsp `basename $1` FT2.fits diffuse_model.xml $irf"
echo \$cmd
\$cmd
if cmp -s $1 `basename $1`
then
  echo Output file identical.. run probably failed
else
  cp `basename $1` $outdir
fi
exit 
EOF

