#!/bin/sh

# qdiffrsp.sh - Send a gtdiffrsp job to the batch queue @ ccin2p3
# Stephen Fegan - sfegan@llr.in2p3.fr - 2008-10-17
# $Id: qdiffrsp.sh 2485 2011-01-21 14:10:43Z sfegan $

if test "$1" == ""
then
  echo "Usage: $0 ft1_file [outdir] [IRF]"
  exit
fi

irf=$3
if test "$irf" == ""
then
  irf=P7SOURCE_V6
fi

if test "$BASEDIR" == ""
then
  BASEDIR=/sps/hep/glast/data/P7.6_P120_BASE
fi
datadir=$BASEDIR/AstroServer
diffdir=$BASEDIR/Diffuse

outdir=$2
if test "$outdir" == ""
then 
  outdir=${DATADIR}/${irf}
fi

gtdiffrsp=$4
if test "$gtdiffrsp" == ""
then
  gtdiffrsp=$(GLAST_BIN)/gtdiffrsp
fi

# When making changes watch the use of $ and \$ in the automaticlly
# generated script given to qsub

#cat <<EOF
qsub <<EOF
#!/bin/bash
#PBS -l t=4286000,M=4096MB,platform=LINUX,scr=30720MB,u_sps_glast
#PBS -eo -V 
### -me -mu sfegan@llr.in2p3.fr

export GLAST_VER=v9r23p1
export GLAST_SYS=redhat5-x86_64-64bit-gcc41
export GLAST_SCI=/afs/in2p3.fr/group/glast/ground/releases/\$GLAST_SYS/ScienceTools/ScienceTools-\$GLAST_VER
export GLAST_BIN=\$GLAST_SCI/bin/\${GLAST_SYS}-Optimized
#export GLAST_REL=/afs/in2p3.fr/group/glast/ground/releases/\$GLAST_SYS/GlastRelease/GlastRelease-v13r13
export GLAST_EXT=/afs/in2p3.fr/group/glast/ground/GLAST_EXT/\$GLAST_SYS
export ROOTSYS=\$GLAST_EXT/ROOT/v5.20.00-gl6/gcc41
export PATH=\$HOME/bin:\$HOME/scripts:\$GLAST_BIN:\$GLAST_REL/bin:/usr/afsws/bin/:\$PATH
export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:/usr/local/lib


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

