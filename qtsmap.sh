#!/bin/bash

# qtsmap.sh - queue a GLAST TS map analysis run on the Lyon cluster
# Stephen Fegan - sfegan@llr.in2p3.fr - 2011-02-14
# $Id$

PWD=`/bin/pwd`
CP='cp -pv'

CMD_RA="$1"
CMD_DEC="$2"
CMD_BINSIZE="$3"
CMD_NPIX="$4"
CMD_NPERJOB="$5"
CMD_NAME=`sanitize_name.sh "$6"`
CMD_DIR="$7"

if test "$CMD_RA" == "" -o "$CMD_DEC" == "" -o "$CMD_BINSIZE" == "" \
     -o "$CMD_NPIX" == "" -o "$CMD_NPERJOB" == "" \
     -o "$CMD_NAME" == "" -o "$CMD_DIR" == ""
then
  echo "usage: $0 ra dec binsize npix nperjob source_name output_directory [settings]"
  exit
fi

ALLARGS="$@"

shift
shift
shift
shift
shift
shift
shift

ARGS="$@"

if test -f $HOME/.analyze_fieldrc
then
  . $HOME/.analyze_fieldrc
fi

if test -f $HOME/.qanalyzerc
then
  . $HOME/.qanalyzerc
fi

RA=`echo $CMD_RA | tr -c '[:digit:]+-.' ' ' | awk 'NF==3{s=1;if(substr($1,0,1)=="-"){s=-1};h=$1;if(h<0){h=-h};printf("%.5f",s*15*(h+($2+$3/60)/60))};NF!=3{print $1}'`
DEC=`echo $CMD_DEC | tr -c '[:digit:]+-.' ' ' | awk 'NF==3{s=1;if(substr($1,0,1)=="-"){s=-1};d=$1;if(d<0){d=-d};printf("%.5f",s*(d+($2+$3/60)/60))};NF!=3{print $1}'`

while test $# -ne 0
do
  var=`echo "$1" | cut -d= -f1`
  if test "$var" == "TIMELIMIT" \
       -o "$var" == "MEMLIMIT" -o "$var" == "SCRLIMIT" \
       -o "$var" == "JOBPREFIX" -o "$var" == "CPUPLATFORM" \
       -o "$var" == "QSUB" -o "$var" == "Q" -o "$var" == "FT2" \
       -o "$var" == "ONEJOB" -o "$var" == "RESTART"
  then
    export "$1"
  fi
  shift
done

if test "$RESTART" \!= ""
then
  RESTART=`echo $RESTART | tr '[:lower:]' '[:upper:]'`
fi

if test "$ONEJOB" \!= ""
then
  ONEJOB=`echo $ONEJOB | tr '[:lower:]' '[:upper:]'`
fi

if test \! -d "$CMD_DIR"
then
  echo Directory does not exists: "$CMD_DIR"
  exit
fi

if test "$Q" \!= ""
then
  if test "$TIMELIMIT"   == ""; then TIMELIMIT=${Q}MAX; fi
  if test "$MEMLIMIT"    == ""; then MEMLIMIT=${Q}MAX; fi
  if test "$SCRLIMIT"    == ""; then SCRLIMIT=${Q}MAX; fi
fi

if test "$TIMELIMIT"   == ""; then TIMELIMIT=GMAX; fi
if test "$TIMELIMIT"   == "MAX"; then TIMELIMIT="TMAX"; fi
if test "$MEMLIMIT"    == ""; then MEMLIMIT=GMAX; fi
if test "$SCRLIMIT"    == ""; then SCRLIMIT=GMAX; fi
if test "$CPUPLATFORM" == ""; then CPUPLATFORM="LINUX"; fi
if test "$JOBPREFIX"   == ""; then JOBPREFIX=TS; fi
if test "$QSUB"        == ""; then QSUB=qsub; fi

# Ref: http://cctools.in2p3.fr/mrtguser/info_bqs_class_config.php

if test "$TIMELIMIT"   == "GMAX"; then TIMELIMIT=680000; fi
if test "$MEMLIMIT"    == "GMAX"; then MEMLIMIT=2048; fi
if test "$SCRLIMIT"    == "GMAX"; then SCRLIMIT=10250; fi

if test "$TIMELIMIT"   == "TMAX"; then TIMELIMIT=4286000; fi
if test "$MEMLIMIT"    == "TMAX"; then MEMLIMIT=3000; fi
if test "$SCRLIMIT"    == "TMAX"; then SCRLIMIT=20480; fi

OUTDIR=`cd "$CMD_DIR"; /bin/pwd`
SCRIPTDIR=`dirname $0`

RAND=`mktemp -u XXXXXXXXXX`

LIMITOPT="-l t=${TIMELIMIT},M=${MEMLIMIT}MB,scr=${SCRLIMIT}MB"
if test "$Q" \!= ""
then
  LIMITOPT="${LIMITOPT} -q $Q"
fi

npix=$((CMD_NPIX*CMD_NPIX))
njob=$(((npix+CMD_NPERJOB-1)/CMD_NPERJOB))
echo "Splitting TS map into $njob jobs"

ijob0=0
ijobN=$njob

if test "$ONEJOB" \!= ""
then
  ijob0=$ONEJOB
  ijobN=$((ijob0+1))
fi

for (( ijob=ijob0; $ijob < $ijobN; ijob=$((ijob+1)) ))
do
  JOBNAME="${JOBPREFIX}_${CMD_NAME}_${ijob}_${RAND}"
  ipix0=$((ijob*CMD_NPERJOB))
  ipixN=$((ipix0+CMD_NPERJOB))
  if `test $ipixN -gt $npix`
  then 
    ipixN=npix
  fi

# *****************************************************************************
# *****************************************************************************
#
# SCRIPT STARTS HERE
#
# *****************************************************************************
# *****************************************************************************

    ${QSUB} <<EOF
#!/bin/bash
#PBS $LIMITOPT
#PBS -l platform=${CPUPLATFORM},u_sps_glast
#PBS -eo 
#PBS -V 
#PBS -N $JOBNAME

###############################################################################
# Script automatically generated by $0 on behalf of $USER
###############################################################################

echo '$0 $ALLARGS'
echo 'Running on:' "`hostname`"
echo 'Uptime:    ' "`uptime`"

#. \$HOME/.bash_profile

if test "\$HEADAS" == ""
then
  export GLAST_SCI="$GLAST_SCI"
  export GLAST_REL="$GLAST_REL"
  export GLAST_EXT="$GLAST_EXT"
  export HEADAS="$HEADAS"
  . \$HEADAS/headas-init.sh
  export PATH=\$HOME/bin:\$HOME/scripts:\$GLAST_SCI/bin:\$GLAST_REL/bin:\$PATH
fi

PFILES=.:\$PFILES
cd \$TMPBATCH

CMD="$CP $OUTDIR/${CMD_NAME}* $OUTDIR/model.xml ."
echo \$CMD
time \$CMD
mv ${CMD_NAME}_model.xml base_${CMD_NAME}_model.xml
$CP $SCRIPTDIR/analyze_field.sh .

if test "$FT2" \\!= ""
then
  time $CP $FT2 ft2.fits
fi

ipix=$ipix0
for (( ipix=$ipix0; \$ipix < $ipixN; ipix=\$((ipix+1)) ))
do
  iypix=\$((ipix/$CMD_NPIX))
  ixpix=\$((ipix-iypix*$CMD_NPIX))
  tiypix=\`awk "BEGIN{printf(\"%03d\",\$iypix)}" /dev/null\`
  tixpix=\`awk "BEGIN{printf(\"%03d\",\$ixpix)}" /dev/null\`

  echo
  echo
  echo "********* IPix = \$ipix (\$tiypix, \$tixpix) *********"

  ZRADEC=\`awk -F, -v ix=\${ixpix} -v iy=\${iypix} -v res=${CMD_BINSIZE} \
                  -v npix=${CMD_NPIX} -v RA=$RA -v Dec=$DEC \
            'BEGIN{pi=2*atan2(1,0);d2r=pi/180;
             x=-(ix-(npix-1)/2)*res;y=(iy-(npix-1)/2)*res;
             r=sqrt(x*x+y*y);d=2*atan2(r*d2r/2,1);p=atan2(y,x);
             sx=sin(d)*cos(p);syy=sin(d)*sin(p);szz=cos(d);
             sz=szz*sin(Dec*d2r)+syy*cos(Dec*d2r);
             sy=szz*cos(Dec*d2r)-syy*sin(Dec*d2r);
             ra=atan2(sx,sy)/d2r+RA;dec=atan2(sz,sqrt(sx*sx+sy*sy))/d2r;
             if(ra>360){ra=ra-360};if(ra<0){ra=ra+360};
             print ra,dec}\' /dev/null\`
  ZRA=\`echo \$ZRADEC|cut -d' ' -f1\`
  ZDEC=\`echo \$ZRADEC|cut -d' ' -f2\`

  echo "Pixel \${tiypix} x \${tixpix}: RA=\$ZRA, Dec=\$ZDEC"
  awk -v Name="ZZZ\${tiypix}x\${tixpix}" -v RA=\$ZRA -v Dec=\$ZDEC \
      'BEGIN{RS="<"};NR>1{if(substr(\$1,1,15)=="/source_library"){printf(\
"  <source name=\"%s\" type=\"PointSource\">\n"\
"    <spectrum type=\"PowerLaw2\">\n"\
"      <parameter free=\"1\" max=\"1000.0\" min=\"1e-05\" name=\"Integral\" scale=\"1e-09\" value=\"1\"/>\n"\
"      <parameter free=\"1\" max=\"-0.5\" min=\"-5.0\" name=\"Index\" scale=\"1.0\" value=\"-2.0\"/>\n"\
"      <parameter free=\"0\" max=\"500000.0\" min=\"20.0\" name=\"LowerLimit\" scale=\"1.0\" value=\"100\"/>\n"\
"      <parameter free=\"0\" max=\"500000.0\" min=\"20.0\" name=\"UpperLimit\" scale=\"1.0\" value=\"100000\"/>\n"\
"    </spectrum>\n"\
"    <spatialModel type=\"SkyDirFunction\">\n"\
"      <parameter free=\"0\" max=\"360.0\" min=\"-360.0\" name=\"RA\" scale=\"1.0\" value=\"%s\"/>\n"\
"      <parameter free=\"0\" max=\"90.0\" min=\"-90.0\" name=\"DEC\" scale=\"1.0\" value=\"%s\"/>\n"\
"    </spatialModel>\n"\
"  </source>\n",Name,RA,Dec);};printf("<%s",\$0)}' base_${CMD_NAME}_model.xml > ${CMD_NAME}_model.xml

  LOGFILE="TS\${tiypix}x\${tixpix}_${CMD_NAME}.log"
#  LOGFILE="${CMD_NAME}_TS\${tiypix}x\${tixpix}.log"

  if test "$RESTART" \\!= "TRUE" -o \\! -f "${OUTDIR}/\$LOGFILE"
  then
    echo "Pixel \${tiypix} x \${tixpix}: RA=\$ZRA, Dec=\$ZDEC" > \$LOGFILE
    echo >> \$LOGFILE

    CMD="./analyze_field.sh $CMD_RA $CMD_DEC $CMD_NAME $ARGS GTLIKEONLY=TRUE RESTART=TRUE"
    if test "$FT2" \\!= ""
    then
      CMD="\$CMD FT2=ft2.fits COPYFT2=FALSE"
    fi

    echo \$CMD
    time bash -c "\$CMD >> \$LOGFILE 2>&1"

    CMD="$CP \$LOGFILE $OUTDIR"
    echo \$CMD
    \$CMD
  else
    echo \$LOGFILE exists... skipping
  fi
done
EOF
done
