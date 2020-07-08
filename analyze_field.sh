#!/bin/bash

# analyze_field.sh - run GLAST analysis on a certain field of view
# Stephen Fegan - sfegan@llr.in2p3.fr - 2008-10-15
# $Id$

# Changelog
#
# 2008-11-21: Removed zmax from gtltcube
# 2008-11-24: Switched to 3-month catalog
# 2008-11-25: Moved catalogs to /sps
# 2008-12-02: Trap SIGUSR1&2 so grace period on CCALI can be used for copying
# 2008-12-04: Print SVN version, command line and gtlike path to output
# 2009-09-14: Integrate changes from Pascal for new analysis tools
#             Implement new public recommendations as per Fermi cicerone
# 2010-03-03: Go to P6_V8
# 2010-04-01: Add simulations option (not April Fools' joke)
# 2010-05-26: Eliminated Pass1/2, just do single pass. O/P files renamed
# 2010-05-26: Option to do gtfindsrc
# 2010-05-27: Option for frozen spectra of catalog sources
# 2010-05-27: Allow users to customize options with ~/.analyze_field
# 2010-07-20: Allow times in MJD or offset in days & RA and DEC in HMS/DMS
# 2010-08-19: Allow custom IRFs to be used with IRFDIR option
# 2010-11-16: Added exposure cube calculation to use with new gtsrcmaps version
# 2011-02-09: Add BINNED analysis mode
# 2011-03-01: Fix major problem with exposure cube in BINNED analysis
# 2011-03-01: Set default rocking and zenith cuts to 52 and 100 deg
# 2011-08-17: Remove unnecessary call to gtsrcmaps in BINNED. Move to P7
# 2011-09-22: Set diffuse source names in model to match FT1 diffuse columns
# 2011-11-23: Add option for TSTART=FIRSTFULLMOON and TEND=MOONPERIOD
# 2015-05-28: Update for Pass 8
# 2016-07-28: Add GTLIKESKIP option to skip gtlike and remaining steps

trap exit SIGUSR1
trap exit SIGUSR2

ECHO=echo
CAT=cat

$ECHO '# ***************************************************************************'
$ECHO '# * $Id$'
$ECHO "# * Command line:  $0" "$@"
$ECHO '# * Start date:  ' "`date`"
$ECHO '# * Using gtlike:' `which gtlike`
$ECHO '# ***************************************************************************'

RA="$1"
DEC="$2"
NAME="$3"

if test "$RA" == "" -o "$DEC" == ""
then
  echo usage $0 ra dec [source_name] [settings]
  exit
fi

if test "$NAME" == "" ; then NAME="unknown" ; fi

# Import settings from the command line
shift
shift
shift

if test -f $HOME/.analyze_fieldrc
then
  $ECHO
  $ECHO '# ---------------------------------------------------------------------'
  $ECHO '# Importing' $HOME/.analyze_fieldrc
  $ECHO '#'
  awk '{print "# >",$0}' $HOME/.analyze_fieldrc | $CAT
  . $HOME/.analyze_fieldrc
  $ECHO '# ---------------------------------------------------------------------'
fi

while test $# -ne 0
do
  export "$1"
  shift
done

if test "$DATAROOT" == ""
then
  DATAROOT=/sps/hep/glast/data/FSSCWeeklyData
fi

if test "$GLAST_EXT" == ""
then
  GLAST_EXT=/sps/hep/glast/ScienceTools/GLAST_EXT/redhat6-x86_64-64bit-gcc44
fi

if test "$CATALOG" == ""
then
  CATALOG=$GLAST_EXT/catalogProducts/v2r2/3FGL/gll_psc_v16.fit
fi

if test "$CLASS" == ""
then
  CLASS="SOURCE"
else
  CLASS=`echo $CLASS | tr '[:lower:]' '[:upper:]'`
fi

if test "$EVCLASS" == ""
then
  if test "$CLASS" == "ULTRACLEANVETO"
  then
    EVCLASS="1024"
  elif test "$CLASS" == "ULTRACLEAN"
  then
    EVCLASS="512"
  elif test "$CLASS" == "CLEAN"
  then
    EVCLASS="256"
  elif test "$CLASS" == "SOURCE"
  then
    EVCLASS="128"
  else
    EVCLASS="0"
  fi
fi

if test "$PARTITION" == ""
then
  PARTITION="FRONTBACK"
else
  PARTITION=`echo $PARTITION | tr '[:lower:]' '[:upper:]'`
fi

EVTYPE_ISO_FILE="_${PARTITION}";

if test "$EVTYPE" == ""
then
  if test "$PARTITION" == "FRONTBACK"
  then
      EVTYPE="3"
      EVTYPE_ISO_FILE=""
  elif test "$PARTITION" == "FRONT"
  then
      EVTYPE="1"
  elif test "$PARTITION" == "BACK"
  then
      EVTYPE="2"
  elif test "$PARTITION" == "PSF"
  then
      EVTYPE="60"
  elif test "$PARTITION" == "PSF0"
  then
      EVTYPE="4"
  elif test "$PARTITION" == "PSF1"
  then
      EVTYPE="8"
  elif test "$PARTITION" == "PSF2"
  then
      EVTYPE="16"
  elif test "$PARTITION" == "PSF3"
  then
      EVTYPE="32"
  elif test "$PARTITION" == "PSF01"
  then
      EVTYPE="12"
  elif test "$PARTITION" == "PSF23"
  then
      EVTYPE="48"
  elif test "$PARTITION" == "PSF012"
  then
      EVTYPE="28"
  elif test "$PARTITION" == "PSF0123" # Same as "PSF"
  then
      EVTYPE="60"
  elif test "$PARTITION" == "EDISP"
  then
      EVTYPE="960"
  elif test "$PARTITION" == "EDISP0"
  then
      EVTYPE="64"
  elif test "$PARTITION" == "EDISP1"
  then
      EVTYPE="128"
  elif test "$PARTITION" == "EDISP2"
  then
      EVTYPE="256"
  elif test "$PARTITION" == "EDISP3"
  then
      EVTYPE="512"
  elif test "$PARTITION" == "EDISP01"
  then
      EVTYPE="192"
  elif test "$PARTITION" == "EDISP23"
  then
      EVTYPE="768"
  elif test "$PARTITION" == "EDISP012"
  then
      EVTYPE="448"
  elif test "$PARTITION" == "EDISP0123" # Same as "EDISP"
  then
      EVTYPE="960"
  else
    EVCLASS="3"
  fi
fi

if test "$IRF" == "";
then
  IRF="P8R2_${CLASS}_V6"
fi

if test "$IRF" == "P8R2_SOURCE_V6"
then
  MMGALNAME="GAL_v02"
  MMISONAME="EG_v02"
else
  MMGALNAME="gal_2yearp7v6_v0"
  MMISONAME="iso_p7v6source"
fi

if test "$DIFFUSEGALACTICMODEL" == ""
then
  DIFFUSEGALACTICMODEL=$GLAST_EXT/diffuseModels/v5r0/gll_iem_v06.fits
else
  MMGALNAME="iso_user"
fi

if test "$ISOTROPICMODEL" == ""
then
  ISOTROPICMODEL=$GLAST_EXT/diffuseModels/v5r0/iso_${IRF}${EVTYPE_ISO_FILE}_v06.txt
else
  MMDISONAME="iso_user"
fi

if test "$COLLISIONAVOID" == ""; then COLLISIONAVOID=0.3; fi

if test "$FT2" == "";
then
  FT2=$DATAROOT/FT2.fits
fi

if test "$FT1" == "";
then
  FT1=@$DATAROOT/FT1_$IRF.dat
fi

if test "$MAKE_MODEL" == "" -o "$MAKE_MODEL" == "sh" -o "$MAKE_MODEL" == "old";
then
  MAKE_MODEL='make_model.sh $RA $DEC $NAME R_OUTER=$CATROI R_INNER=$COLLISIONAVOID R_FROZEN=$CATFROZENROI CATALOG=$CATALOG DIFFGAL=$DIFFUSEGALACTICMODEL DGNAME=$MMGALNAME DIFFISO=$ISOTROPICMODEL DINAME=$MMISONAME EMIN=$EMIN EMAX=$EMAX MODEL=$MODEL REGION=$ROITYPE TSCUT=$CATTSCUT'
elif test "$MAKE_MODEL" == "py" -o "$MAKE_MODEL" == "new";
then
  MAKE_MODEL='make_model.py --outer=$ROI --inner=$COLLISIONAVOID --catalog=$CATALOG --emin=$EMIN --emax=$EMAX -- $RA $DEC $NAME'
fi

if test "$SIM" == "";            then SIM=FALSE; fi
if test "$ANALYSIS" == "";       then ANALYSIS=UNBINNED; fi
if test "$SIMIRF" == "";         then SIMIRF="$IRF"; fi
if test "$GTLIKESKIP" == "";     then GTLIKESKIP=FALSE; fi
if test "$GTLIKEONLY" == "";     then GTLIKEONLY=FALSE; fi
if test "$FORCEDIFFRSP" == "";   then FORCEDIFFRSP=FALSE; fi
if test "$COMPUTEPTSRCMAP" = ""; then COMPUTEPTSRCMAP=TRUE; fi

if test "$FINDSRC" == "";        then FINDSRC=""; fi
if test "$FINDSRCPOSNTOL" == ""; then FSPOSNTOL=0.01; fi
if test "$FINDSRCLIKETOL" == ""; then FSLIKETOL=0.01; fi

if test "$MODEL" == "";          then MODEL=PL2; fi
if test "$EMIN" == "";           then EMIN=100; fi
if test "$EMAX" == "";           then EMAX=500000; fi
if test "$ZMAX" == "";           then ZMAX=90; fi
if test "$ROCK_MAX" == "";       then ROCK_MAX=180; fi
if test "$ROICUT" == "";         then ROICUT="NO"; fi
if test "$ROI" == "";            then ROI=10.0; fi
if test "$OPT" == "";            then OPT=MINUIT; fi
if test "$TOL" == "";            then TOL=1e-4; fi
if test "$TSTART" == "";         then TSTART=0; fi
if test "$TEND" == "";           then TEND=0; fi
if test "$BINSIZE" == "";        then BINSIZE=0.1; fi
if test "$RUN" == "" -o "$RUN" == "true"; then RUN=""; fi
if test "$RESTART" == "";        then RESTART=""; fi
if test "$COPYFT2" == "";        then COPYFT2="TRUE"; fi

# Legacy support of pass1 and pass2 options
if test "$P1OPT" \!= "";         then OPT=$P1OPT; fi
if test "$P1TOL" \!= "";         then TOL=$P1TOL; fi
if test "$P2OPT" \!= "";         then OPT=$P2OPT; fi
if test "$P2TOL" \!= "";         then TOL=$P2TOL; fi

if test "$CATTSCUT" == "";
then
  CATTSCUT=0
fi

if test "$CATROI" == "";
then
  CATROI=`echo "scale=0;$ROI+2.0" | bc`
fi

if test "$CATFROZENROI" == "";
then
  CATFROZENROI=$ROI
fi

SIM=`echo $SIM | tr '[:lower:]' '[:upper:]'`
ANALYSIS=`echo $ANALYSIS | tr '[:lower:]' '[:upper:]'`
GTLIKEONLY=`echo $GTLIKEONLY | tr '[:lower:]' '[:upper:]'`
GTLIKESKIP=`echo $GTLIKESKIP | tr '[:lower:]' '[:upper:]'`
FORCEDIFFRSP=`echo $FORCEDIFFRSP | tr '[:lower:]' '[:upper:]'`
COMPUTEPTSRCMAP=`echo $COMPUTEPTSRCMAP | tr '[:lower:]' '[:upper:]'`
ROICUT=`echo $ROICUT | tr '[:lower:]' '[:upper:]'`

DSROI="$ROI"
ROITYPE="CIRCLE"
if test "$ANALYSIS" == "BINNED"
then
  DSROI=`echo "scale=0;$ROI*1.42" | bc`
  ROITYPE="SQUARE"
fi

if test "$CONE" == "";
then
  CONE=`echo "scale=0;$DSROI+10.0" | bc`
fi

if test "$NEGY" == "";
then
  NEGY=`awk "BEGIN{print int(log($EMAX/$EMIN)/2.30258*10+0.5);}" /dev/null`
  if test "$NEGY" -lt 5
  then
    NEGY=5
  fi
fi

if test "$SIMSEED" == "";
then
  SIMSEED=`head -c4 /dev/random | od -t u4 | awk 'NR==1{print $2}'`
fi

ROI_NPIX=`echo "scale=0;$ROI/$BINSIZE*2" | bc`
CONE_NPIX=`echo "scale=0;$CONE/$BINSIZE*2" | bc`
CONE_NPIX_EXPMAP=`echo "scale=0;$CONE/0.5*2" | bc`

if test "$TSTART" == "NOMSCIOP" -o "$TSTART" == "NOMSCIOPS"
then
    TSTART=239557414
elif test "$TSTART" == "FIRSTFULLMOON"
then
    TSTART=54694.888
fi

if test "$TSTART" \!= "0" -a `echo "$TSTART<100000"|bc` == "1"
then
    TSTART=`echo "(($TSTART-51910)*86400+0.5)/1"|bc`
fi

if test "$TEND" == "MOONPERIOD"
then
    TEND=29.530589
elif test "$TEND" == "MOONPERIOD_2"
then
    TEND=14.76529
elif test "$TEND" == "MOONPERIOD_4"
then
    TEND=7.382647
fi

if test "$TEND" \!= "0" -a `echo "$TEND<10000"|bc` == "1"
then
    TEND=`echo "$TSTART+($TEND*86400+0.5)/1"|bc`
fi

if test "$TEND" \!= "0" -a `echo "$TEND<100000"|bc` == "1"
then
    TEND=`echo "(($TEND-51910)*86400+0.5)/1"|bc`
fi

if test "$LCBIN" \!= ""
then
    TDELTA=`echo "($TEND-$TSTART+0.5)/1"|bc`
    TOFFSET=`echo "($LCBIN*$TDELTA+0.5)/1"|bc`
    TOFFSETDAY=`echo "scale=3;$TOFFSET/86400"|bc`
    TSTART=`echo "($TSTART+$TOFFSET+0.5)/1"|bc`
    TEND=`echo "($TEND+$TOFFSET+0.5)/1"|bc`
fi

RA=`echo $RA | tr -c '[:digit:]+-.' ' ' | awk 'NF==3{s=1;if(substr($1,0,1)=="-"){s=-1};h=$1;if(h<0){h=-h};printf("%.5f",s*15*(h+($2+$3/60)/60))};NF!=3{print $1}'`
DEC=`echo $DEC | tr -c '[:digit:]+-.' ' ' | awk 'NF==3{s=1;if(substr($1,0,1)=="-"){s=-1};d=$1;if(d<0){d=-d};printf("%.5f",s*(d+($2+$3/60)/60))};NF!=3{print $1}'`

RAHMS=`echo $RA | awk '{h=$1/15;printf("%02dh%02dm%04.1fs",int(h),int(h*60)%60,h*3600%60)}'`
DECDMS=`echo $DEC | awk '{d=$1;s="+";if(d<0){d=-d;s="-"};printf("%c%03dd%02dm%04.1fs",s,int(d),int(d*60)%60,d*3600%60)}'`

MJDSTART="-inf"
UTCSTART="-inf"
if test "$TSTART" \!= "0"
then
    MJDSTART=`echo "scale=5;$TSTART/86400.0+51910.0"|bc`
    UTCSTART=`date -u -d @$((TSTART+978307200)) +"%Y-%m-%d %H:%M"`
fi

MJDEND="inf"
UTCEND="inf"
TDUR="an unknown number of"
if test "$TEND" \!= "0"
then
    MJDEND=`echo "scale=5;$TEND/86400.0+51910.0"|bc`
    UTCEND=`date -u -d @$((TEND+978307200)) +"%Y-%m-%d %H:%M"`
    if test "$TSTART" \!= "0"
    then
        TDUR=`echo "scale=5;$MJDEND-$MJDSTART"|bc`
    fi
fi

RESTART=`echo $RESTART | tr '[:lower:]' '[:upper:]'`

REUSEFIT=""
if test "$RESTART" == "FIT" -o "$RESTART" == "PASS1" -o "$RESTART" == "PASS2"
then
  REUSEFIT="TRUE"
  RESTART="TRUE"
fi

UCOPT=`echo $OPT | tr '[:lower:]' '[:upper:]'`
COPYFT2=`echo $COPYFT2 | tr '[:lower:]' '[:upper:]'`

if test "$IRFDIR" \!= ""
then
  export CUSTOM_IRF_DIR="$IRFDIR"
  export CUSTOM_IRF_NAMES="$IRF"
fi

TRUN="$RUN time"

$ECHO
$ECHO '# ***************************************************************************'
$ECHO '# * 0 - Run settings'
$ECHO '# *'
$ECHO "# * Name:         $NAME"
$ECHO "# * RA:           $RA deg, $RAHMS"
$ECHO "# * Dec:          $DEC deg, $DECDMS"
$ECHO "# * Sim mode:     $SIM (opt: SIM)"
$ECHO "# * Analysis:     $ANALYSIS (opt: ANALYSIS)"
$ECHO "# * Model:        $MODEL (opt: MODEL)"
if test "$LCBIN" \!= ""
then
  $ECHO "# * LCBin:        $LCBIN - offset: $TOFFSET sec, $TOFFSETDAY day (opt: LCBIN)"
else
  $ECHO "# * LCBin:        No lightcurve binning offset applied (opt: LCBIN)"
fi
$ECHO "# * TStart:       MET:$TSTART, MJD:$MJDSTART (opt: TSTART)"
$ECHO "# * TEnd:         MET:$TEND, MJD:$MJDEND (opt: TEND)"
$ECHO "# * UTCRange:     $UTCSTART to $UTCEND, $TDUR days"
$ECHO "# * EMin:         $EMIN MeV (opt: EMIN)"
$ECHO "# * EMax:         $EMAX MeV (opt: EMAX)"
if test "$IRFDIR" \!= ""
then
  $ECHO "# * Custom IRF:   $IRFDIR (opt: IRFDIR)"
else
  $ECHO "# * Custom IRF:   No custom IRF directory set (opt: IRFDIR)"
fi
$ECHO "# * IRF:          $IRF (opt: IRF)"
$ECHO "# * ZMax:         $ZMAX deg (opt: ZMAX)"
$ECHO "# * RockMax:      $ROCK_MAX deg (opt: ROCKMAX)"
$ECHO "# * ROI:          $ROI deg (opt: ROI)"
$ECHO "# * Data ROI:     $DSROI deg"
$ECHO "# * CatROI:       $CATROI deg (opt: CATROI)"
$ECHO "# * CatFrozenROI: $CATFROZENROI deg (opt: CATFROZENROI)"
$ECHO "# * CatTSCut:     $CATTSCUT (opt: CATTSCUT)"
$ECHO "# * Cone:         $CONE deg (opt: CONE)"
$ECHO "# * Class:        $CLASS / $EVCLASS (opt: CLASS / EVCLASS)"
$ECHO "# * Partition:    $PARTITION / $EVTYPE (opt: PARTITION / EVTYPE)"
$ECHO "# * Catalog:      $CATALOG (opt: CATALOG)"
$ECHO "# * DiffuseGal:   $DIFFUSEGALACTICMODEL (opt: DIFFUSEGALACTICMODEL)"
$ECHO "# * DiffuseIso:   $ISOTROPICMODEL (opt: ISOTROPICMODEL)"
if test "$SIM" == "TRUE";
then
$ECHO "# * SimIRF:       $SIMIRF (opt: SIMIRF)"
$ECHO "# * SimSeed:      $SIMSEED (opt: SIMSEED)"
else
$ECHO "# * FT1:          $FT1 (opt: FT1)"
fi
$ECHO "# * FT2:          $FT2 (opt: FT2)"
$ECHO "# * Copy FT2      $COPYFT2 (opt: COPYFT2)"
$ECHO "# * Optimizer:    $OPT (opt: OPT)"
$ECHO "# * Tolerance     $TOL (opt: TOL)"
$ECHO "# * NEnergyBin:   $NEGY (opt: NEGY)"
$ECHO "# * SpatialBinSz: $BINSIZE (opt: BINSIZE)"
$ECHO "# * ForceDiffRsp: $FORCEDIFFRSP (opt: FORCEDIFFRSP)"
$ECHO "# * CompPtSrcMap: $COMPUTEPTSRCMAP (opt: COMPUTEPTSRCMAP)"
if test "$FINDSRC" != "";
then
$ECHO "# * FindSrc:      $FINDSRC (opt: FINDSRC)"
$ECHO "# * FSLikeTol:    $FINDSRCLIKETOL (opt: FINDSRCLIKETOL)"
$ECHO "# * FSPosnTol:    $FINDSRCPOSNTOL (opt: FINDSRCPOSNTOL)"
fi
$ECHO '# *****************************************************************************'

if test "$COPYFT2" == "TRUE"
then
  $ECHO
  CMD="rm -f ft2.fits"
  $ECHO $CMD
  $RUN $CMD
  CMD="cp -p $FT2 ft2.fits"
  $ECHO $CMD
  $TRUN $CMD
  FT2=ft2.fits
fi

$ECHO
$ECHO '# *****************************************************************************'
$ECHO '# * 1 - Make model file(s)'
$ECHO '# *****************************************************************************'

CMD=`eval echo $MAKE_MODEL`
if test \! -f ${NAME}_model.xml
then
  if test -f model.xml
  then
    $ECHO cp model.xml ${NAME}_model.xml
    $RUN cp model.xml  ${NAME}_model.xml
  else
    $ECHO $CMD '>' ${NAME}_model.xml
    $RUN bash -c "$CMD > ${NAME}_model.xml"
  fi
else
  $ECHO $CMD '>' ${NAME}_model.xml
  $ECHO ${NAME}_model.xml already exists ... skipping
fi

if test "$SIM" == "TRUE"
then
  CMD="convert_gtlike_model_to_gtobssim.awk ${NAME}_model.xml"
  $ECHO $CMD '>' ${NAME}_sim_model.xml
  if test \! -f ${NAME}_sim_model.xml
  then
    $RUN bash -c "$CMD > ${NAME}_sim_model.xml"
  else
    $ECHO ${NAME}_sim_model.xml already exists ... skipping
  fi
fi

$ECHO
$ECHO '# *****************************************************************************'
$ECHO '# * 2 - Select data from library or simulate - GTSELECT or GTOBSSIM'
$ECHO '# *****************************************************************************'

if test "$SIM" == "TRUE"
then
  simstartdate=`date -u -d @$((TSTART+978307200)) +"%Y-%m-%d %H:%M:%S"`
  CMD="gtobssim infile=${NAME}_sim_model.xml srclist=${NAME}_sim_source_names.txt scfile=$FT2 evroot=${NAME}_sim simtime=$((TEND-TSTART)) startdate=\"$simstartdate\" use_ac=true ra=$RA dec=$DEC radius=$DSROI emin=$EMIN emax=$EMAX irfs=$SIMIRF seed=$SIMSEED"
  $ECHO $CMD
  if test \( -f ${NAME}_ev_roi_raw.fits -o -f ${NAME}_ev_roi.fits \) -a "$RESTART" == "TRUE"
  then
    echo "Skipping"
  else
    CMD2="rm -f ${NAME}_sim_events_*.fits"
    $ECHO $CMD2
    $RUN $CMD2
    grep '<source ' ${NAME}_sim_model.xml | sed -e 's/.*name="\([^"]*\)".*/\1/' > ${NAME}_sim_source_names.txt
    $TRUN bash -c "$CMD"
    CMD="rm -f ${NAME}_ev_roi_raw.fits"
    $ECHO $CMD
    $RUN $CMD
    if test -f ${NAME}_sim_events_0001.fits
    then
      sim_events=`echo ${NAME}_sim_events_*.fits | tr ' ' ','`
      CMD="ftmerge infile=$sim_events outfile=${NAME}_ev_roi_raw.fits"
    else
      CMD="cp ${NAME}_sim_events_0000.fits ${NAME}_ev_roi_raw.fits"
    fi
    $ECHO $CMD
    $RUN $CMD
  fi
else
  CMD="gtselect infile=$FT1 outfile=${NAME}_ev_roi_raw.fits ra=$RA dec=$DEC rad=$DSROI tmin=$TSTART tmax=$TEND emin=$EMIN emax=$EMAX zmax=$ZMAX evclass=$EVCLASS evtype=$EVTYPE"
  $ECHO $CMD
  if test \( -f ${NAME}_ev_roi_raw.fits -o -f ${NAME}_ev_roi.fits \) -a "$RESTART" == "TRUE"
  then
    echo "Skipping"
  else
    $TRUN $CMD
  fi
fi

$ECHO
$ECHO '# *****************************************************************************'
$ECHO '# * 3 - Update the GTI and cut data based on ROI - GTMKTIME'
$ECHO '# *****************************************************************************'
CMD="gtmktime scfile=$FT2 filter=(DATA_QUAL>0)&&(LAT_CONFIG==1)&&abs(ROCK_ANGLE)<$ROCK_MAX roicut=$ROICUT evfile=${NAME}_ev_roi_raw.fits outfile=${NAME}_ev_roi.fits"
$ECHO $CMD
if test -f ${NAME}_ev_roi.fits -a "$RESTART" == "TRUE"
then
  echo "Skipping"
else
  $TRUN $CMD
fi

$ECHO
$ECHO '# *****************************************************************************'
$ECHO '# * 4 - Make counts map and cube or user to look at - GTBIN'
$ECHO '# *****************************************************************************'
CMD="gtbin evfile=${NAME}_ev_roi.fits scfile=$FT2 outfile=${NAME}_map.fits algorithm=CMAP nxpix=$ROI_NPIX nypix=$ROI_NPIX binsz=$BINSIZE coordsys=CEL xref=$RA yref=$DEC axisrot=0 proj=STG"
$ECHO $CMD
if test -f ${NAME}_map.fits -a "$RESTART" == "TRUE"
then
  echo "Skipping"
else
  $TRUN $CMD
fi
CMD="gtbin evfile=${NAME}_ev_roi.fits scfile=$FT2 outfile=${NAME}_ccube.fits algorithm=CCUBE nxpix=$ROI_NPIX nypix=$ROI_NPIX binsz=$BINSIZE coordsys=CEL xref=$RA yref=$DEC axisrot=0 proj=STG ebinalg=LOG emin=$EMIN emax=$EMAX enumbins=$NEGY"
$ECHO $CMD
if test -f ${NAME}_ccube.fits -a "$RESTART" == "TRUE"
then
  echo "Skipping"
else
  $TRUN $CMD
fi
CMD="gtbin evfile=${NAME}_ev_roi.fits scfile=$FT2 outfile=${NAME}_extended_ccube.fits algorithm=CCUBE nxpix=$CONE_NPIX nypix=$CONE_NPIX binsz=$BINSIZE coordsys=CEL xref=$RA yref=$DEC axisrot=0 proj=STG ebinalg=LOG emin=$EMIN emax=$EMAX enumbins=$NEGY"
$ECHO $CMD
if test -f ${NAME}_extended_ccube.fits -a "$RESTART" == "TRUE"
then
  echo "Skipping"
else
  $TRUN $CMD
fi

$ECHO
$ECHO '# *****************************************************************************'
$ECHO '# * 5 - Make live time cube - GTLTCUBE'
$ECHO '# *****************************************************************************'
CMD="gtltcube evfile=${NAME}_ev_roi.fits scfile=$FT2 outfile=${NAME}_expCube.fits dcostheta=0.025 binsz=1"
if test "$ROICUT" == "NO"
then
    CMD="$CMD zmax=$ZMAX"
fi
$ECHO $CMD
if test -f ${NAME}_expCube.fits -a "$RESTART" == "TRUE"
then
  echo "Skipping"
else
  $TRUN $CMD
fi

$ECHO
$ECHO '# *****************************************************************************'
$ECHO '# * 6 - Make exposure map - GTEXPMAP'
$ECHO '# *****************************************************************************'
if test "$ANALYSIS" == "BINNED"
then
  $ECHO "Skipping in BINNED analysis mode"
else
  CMD="gtexpmap evfile=${NAME}_ev_roi.fits scfile=$FT2 expcube=${NAME}_expCube.fits outfile=${NAME}_expMap.fits irfs=$IRF srcrad=$CONE nlong=$CONE_NPIX_EXPMAP nlat=$CONE_NPIX_EXPMAP nenergies=$NEGY"
  $ECHO $CMD
  if test -f ${NAME}_expMap.fits -a "$RESTART" == "TRUE"
  then
    echo "Skipping"
  else
    $TRUN $CMD
  fi
fi

$ECHO
$ECHO '# *****************************************************************************'
$ECHO '# * 7 - Make binned exposure cube - GTEXPCUBE2'
$ECHO '# *****************************************************************************'
CMD="gtexpcube2 infile=${NAME}_expCube.fits cmap=${NAME}_extended_ccube.fits outfile=${NAME}_binExpMap.fits irfs=$IRF bincalc=EDGE emin=$EMIN emax=$EMAX enumbins=$NEGY"
$ECHO $CMD
if test -f ${NAME}_binExpMap.fits -a "$RESTART" == "TRUE"
then
  echo "Skipping"
else
  $TRUN $CMD
fi

if test "$ANALYSIS" == "BINNED"
then
  $ECHO
  $ECHO '# *****************************************************************************'
  $ECHO '# * 8 - Binned source maps - GTSRCMAPS'
  $ECHO '# *****************************************************************************'
  if test "$COMPUTEPTSRCMAP" == "FALSE" -o "$COMPUTEPTSRCMAP" == "NO"
  then
    COMPUTEPTSRCMAP=no
  else
    COMPUTEPTSRCMAP=yes
  fi
  CMD="gtsrcmaps scfile=$FT2 expcube=${NAME}_expCube.fits cmap=${NAME}_ccube.fits srcmdl=${NAME}_model.xml bexpmap=${NAME}_binExpMap.fits outfile=${NAME}_srcMaps.fits irfs=$IRF ptsrc=${COMPUTEPTSRCMAP}"
  $ECHO $CMD
  if test -f ${NAME}_srcMaps.fits -a "$RESTART" == "TRUE"
  then
    echo "Skipping"
  else
    $TRUN $CMD
  fi
else
  $ECHO
  $ECHO '# *****************************************************************************'
  $ECHO '# * 8 - Compute the diffuse response - GTDIFFRP'
  $ECHO '# *****************************************************************************'
  CMD="gtdiffrsp evfile=${NAME}_ev_roi.fits scfile=$FT2 srcmdl=${NAME}_model.xml irfs=$IRF convert=yes"
  if test "$FORCEDIFFRSP" == "TRUE"
  then
    CMD="$CMD clobber=yes"
  fi
  $ECHO $CMD
  $TRUN $CMD
fi

$ECHO
$ECHO '# *****************************************************************************'
$ECHO '# * 9 - Likelihood analysis - GTLIKE'
$ECHO '# *****************************************************************************'
if test "$ANALYSIS" == "BINNED"
then
  GTLIKEOPT="statistic=BINNED cmap=${NAME}_srcMaps.fits bexpmap=${NAME}_binExpMap.fits"
else
  GTLIKEOPT="statistic=UNBINNED evfile=${NAME}_ev_roi.fits scfile=$FT2 expmap=${NAME}_expMap.fits"
fi
CMD="gtlike $GTLIKEOPT irfs=$IRF expcube=${NAME}_expCube.fits srcmdl=${NAME}_model.xml sfile=${NAME}_fitmodel.xml results=${NAME}_results.dat specfile=${NAME}_counts_spectra.fits optimizer=$OPT ftol=$TOL toltype=ABS tsmin=no chatter=3"
$ECHO $CMD
if test "$GTLIKESKIP" \!= "TRUE"
then
  if test -f ${NAME}_fitmodel.xml -a "$REUSEFIT" == "TRUE"
  then
    echo "Skipping"
  else
    $TRUN $CMD
  fi
else
  echo "Skipping as requested"
fi

if test "$GTLIKESKIP" \!= "TRUE"
then
  if test "$GTLIKEONLY" \!= "TRUE"
  then
    $ECHO
    $ECHO '# *****************************************************************************'
    $ECHO '# * 10 - Binned source maps - GTSRCMAPS'
    $ECHO '# *****************************************************************************'
    if test "$ANALYSIS" == "BINNED"
    then
      $ECHO "Already completed in BINNED analysis mode"
    else
      CMD="gtsrcmaps scfile=$FT2 expcube=${NAME}_expCube.fits cmap=${NAME}_ccube.fits srcmdl=${NAME}_fitmodel.xml bexpmap=${NAME}_binExpMap.fits outfile=${NAME}_srcMaps.fits irfs=$IRF"
      $ECHO $CMD
      $TRUN $CMD
    fi

    $ECHO
    $ECHO '# *****************************************************************************'
    $ECHO '# * 11 - Background maps - GTMODEL'
    $ECHO '# *****************************************************************************'
    CMD="gtmodel srcmaps=${NAME}_srcMaps.fits srcmdl=${NAME}_fitmodel.xml outfile=${NAME}_modelmap.fits irfs=$IRF expcube=${NAME}_expCube.fits bexpmap=${NAME}_binExpMap.fits"
    $ECHO $CMD
    $TRUN $CMD
    $RUN rm -f residualmap.fits
    CMD="farith ${NAME}_map.fits ${NAME}_modelmap.fits residualmap.fits SUB"
    $ECHO $CMD
    $RUN $CMD
    $RUN mv residualmap.fits ${NAME}_residualmap.fits
  fi

  if test "$FINDSRC" \!= "";
  then
    $ECHO
    $ECHO '# *****************************************************************************'
    $ECHO '# * 12 - Find source - GTFINDSRC'
    $ECHO '# *****************************************************************************'
    if test "$ANALYSIS" == "BINNED"
    then
      $ECHO
      $ECHO "GTFINDSRC is incompatible with ${ANALYSIS} analysis ... skipping"
    else
      for target in `echo $FINDSRC | tr ',' ' '`
      do
        if test "$target" == "-"; then target="$NAME"; fi
        $ECHO
        $ECHO '# -------------------------------------------'
        $ECHO "# TARGET: $target"
        $ECHO '# -------------------------------------------'

        CMD="gtfindsrc evfile=${NAME}_ev_roi.fits scfile=$FT2 outfile=${NAME}_findSrc_${target}.out irfs=$IRF expcube=${NAME}_expCube.fits expmap=${NAME}_expMap.fits srcmdl=${NAME}_fitmodel.xml target=$target optimizer=$OPT ftol=$FINDSRCLIKETOL atol=$FINDSRCPOSNTOL toltype=ABS chatter=3"
        $ECHO $CMD
        $TRUN $CMD
      done
    fi
  fi
fi

if test "$COPYFT2" == "TRUE"
then
  $ECHO
  CMD="rm -f ft2.fits"
  $ECHO $CMD
  $RUN $CMD
fi

$ECHO
$ECHO Fin...
