#!/bin/bash

# make_model.sh - make a model file from a catalog FITS file
# Stephen Fegan - sfegan@llr.in2p3.fr - 2008-10-15
# $Id: make_model_1fgl.sh 4775 2012-11-16 07:51:09Z sfegan $

# Changelog
#
# 2009-09-14 SF: Integrated PF's changes for new diffuse extragalatic
# 2009-09-15 SF: Fixed problems with index in new catalog (sign and limits)
# 2009-09-28 PF: Changed scaling of catalog source fluxes to 10^-9
# 2009-10-01 PF: Fixed bug with the scaling of the flux
# 2009-10-07 SF: Added option to use PL1
# 2010-05-27 SF: Added radius to freeze spectra of catalog sources
# 2010-10-21 SF: Change to using Pivot_Energy and Flux_Density
# 2011-02-09 SF: Add option for square ROIs

function catalog {
  r_inner=$1
  r_outer=$2
  free=$3
  mode=$4
  fdump $CATALOG"[1][angsep(RA,DEC,$RA,$DEC)<$r_outer*1.42 && angsep(RA,DEC,$RA,$DEC)>=$r_inner]" STDOUT NickName,RA,DEC,Pivot_Energy,Flux_Density,Spectral_Index - prhead=no showunit=no showrow=no showcol=no pagewidth=256 page=no fldsep="," | \
    sed -e '/^ *$/d;s/ *, */,/g' | \
    awk -F, -v Elo=$EMIN -v Ehi=$EMAX -v Free=$free -v Mode=$mode \
            -v Ri=$r_inner -v Ro=$r_outer -v RA=$RA -v Dec=$DEC\
        'BEGIN{pi=2*atan2(1,0);d2r=pi/180;}\
         {szz=sin($3*d2r);sxx=cos($3*d2r)*cos(($2-RA)*d2r);sy=cos($3*d2r)*sin(($2-RA)*d2r);
          sz=szz*sin(Dec*d2r)+sxx*cos(Dec*d2r); sx=-szz*cos(Dec*d2r)+sxx*sin(Dec*d2r);
	  t=atan2(sqrt(sx*sx+sy*sy),sz)/d2r;
          r=2/d2r*(1-sz)/sqrt(sx*sx+sy*sy);p=atan2(sy,sx);x=r*cos(p);y=r*sin(p);
          if(Mode==1){xymax=sqrt(x*x);if(sqrt(y*y)>xymax){xymax=sqrt(y*y)};inregion=xymax<Ro&&xymax>=Ri;}
          else{inregion=r<Ro&&r>=Ri;};if(0){print $1,x,y,r,t,inregion,Ri,Ro;}
          idx=$6; if(idx<0.51){idx=0.51;};if(idx>4.9){idx=4.9;};idx=-idx;
          Ep=$4;F0=$5;J=F0*Ep/(idx+1)*((Ehi/Ep)**(idx+1)-(Elo/Ep)**(idx+1));S=10**(int(log(J)/log(10)));
          if(inregion){printf("  <source name=\"%s\" type=\"PointSource\">\n"\
"    <spectrum type=\"PowerLaw2\">\n"\
"      <parameter free=\"%d\" max=\"1000.0\" min=\"1e-05\" name=\"Integral\" scale=\"%.0e\" value=\"%f\"/>\n"\
"      <parameter free=\"%d\" max=\"-0.5\" min=\"-5.0\" name=\"Index\" scale=\"1.0\" value=\"%.3f\"/>\n"\
"      <parameter free=\"0\" max=\"500000.0\" min=\"20.0\" name=\"LowerLimit\" scale=\"1.0\" value=\"%d\"/>\n"\
"      <parameter free=\"0\" max=\"500000.0\" min=\"20.0\" name=\"UpperLimit\" scale=\"1.0\" value=\"%d\"/>\n"\
"    </spectrum>\n"\
"    <spatialModel type=\"SkyDirFunction\">\n"\
"      <parameter free=\"0\" max=\"360.0\" min=\"-360.0\" name=\"RA\" scale=\"1.0\" value=\"%.3f\"/>\n"\
"      <parameter free=\"0\" max=\"90.0\" min=\"-90.0\" name=\"DEC\" scale=\"1.0\" value=\"%.3f\"/>\n"\
"    </spatialModel>\n"\
"  </source>\n",$1,Free,S,J/S,Free,idx,Elo,Ehi,$2,$3)}}'
}

RA=$1
DEC=$2
NAME=$3

R_OUTER=10
R_INNER=0.3
R_FROZEN=180.0
CATALOG=/sps/hep/glast/users/sfegan/newdata/catalog.fits
DIFFGAL=/sps/hep/glast/users/sfegan/newdata/diffuse_galactic.fits
DIFFISO=/sps/hep/glast/users/sfegan/newdata/isotropic.txt
EMIN=100
EMAX=300000
MODEL=PL2
REGION=CIRCLE
RMODE=0

if test "$RA" == ""
then
  cat <<EOF
usage: $0 RA DEC NAME [OPTIONS...]

where:
RA      - Right ascension of test source
DEC     - Declination of test source
NAME    - Name of test source

and OPTIONS is a set of optional parameters given in NAME=VALUE form.
The following options are recognised

REGION   - Region type (CIRCLE or SQUARE)         [$REGION]
R_OUTER  - Outer radius for catalog source        [$R_OUTER deg]
R_INNER  - Inner radius for catalog source        [$R_INNER deg]
R_FROZEN - Radius to freeze catalog sources       [$R_FROZEN deg]
CATALOG  - FITS file with source catalog          [$CATALOG]
DIFFGAL  - FITS file with galactic model          [$DIFFGAL]
DIFFISO  - Text file with isotropic diffuse model [$DIFFISO]
EMIN     - Minimum energy                         [$EMIN MeV]
EMAX     - Maximum energy                         [$EMAX MeV]
MODEL    - Type of model to use (PL1 or PL2)      [$MODEL]
EREF     - Reference energy for PL1               [sqrt(EMIN*EMAX)]
EOF
  exit
fi

# Import settings from the command line
shift
shift
shift

while test $# -ne 0
do
  export "$1"
  shift
done

if test "$EREF" == ""; then EREF=`echo "scale=0;sqrt($EMIN*$EMAX)" | bc -l`; fi
if test "$REGION" == "SQUARE"; then RMODE=1; fi

#
# Make the model
#

cat <<'EOF'
<?xml version="1.0" ?><source_library title="source library">
EOF

# DIFFGAL *********************************************************************

#    <spectrum type="PowerLaw">
#      <parameter free="1" max="1000.0" min="1e-3" name="Prefactor" scale="1.0" value="1.0"/>
#      <parameter free="1" max="1" min="-1" name="Index" scale="1.0" value="0"/>
#      <parameter free="0" max="2000" min="50" name="Scale" scale="1" value="100"/>

if test "$DIFFGAL" \!= "none"
then
  cat <<EOF
  <source name="GAL_v02" type="DiffuseSource">
<!-- diffuse source units are cm^-2 s^-1 MeV^-1 sr^-1 -->
    <spectrum type="ConstantValue">
      <parameter free="1" max="100.0" min="0.01" name="Value" scale="1.0" value="1.0"/>
    </spectrum>
    <spatialModel file="$DIFFGAL" type="MapCubeFunction">
      <parameter free="0" max="1000.0" min="0.001" name="Normalization" scale="1.0" value="1.0"/>
    </spatialModel>
  </source>
EOF
fi

# EXTRAGALACTIC DIFFUSE *******************************************************

if test "$DIFFISO" == ""
then
  cat <<EOF
  <source name="EG_pl" type="DiffuseSource">
    <spectrum type="PowerLaw">
      <parameter free="1" max="100.0" min="1e-05" name="Prefactor" scale="1e-07" value="1.6"/>
      <parameter free="1" max="-1.0" min="-3.5" name="Index" scale="1.0" value="-2.1"/>
      <parameter free="0" max="200.0" min="50.0" name="Scale" scale="1.0" value="100.0"/>
    </spectrum>
    <spatialModel type="ConstantValue">
      <parameter free="0" max="10.0" min="0.0" name="Value" scale="1.0" value="1.0"/>
    </spatialModel>
  </source>
EOF
elif test "$DIFFISO" \!= "none"
then
  cat <<EOF
  <source name="EG_v02" type="DiffuseSource">
    <spectrum file="$DIFFISO" type="FileFunction">
      <parameter free="1" max="100.0" min="0.01" name="Normalization" scale="1" value="1.0"/>
    </spectrum>
    <spatialModel type="ConstantValue">
      <parameter free="0" max="10.0" min="0.0" name="Value" scale="1.0" value="1.0"/>
    </spatialModel>
  </source>
EOF
fi

# TEST SOURCE *****************************************************************

cat <<EOF
  <source name="$NAME" type="PointSource">
EOF

if test "$MODEL" == "PL1"
then
  cat <<EOF
<!-- point source units are cm^-2 s^-1 MeV^-1 -->
    <spectrum type="PowerLaw">
      <parameter free="1" max="10000.0" min="1e-05" name="Prefactor" scale="1e-12" value="2.0"/>
      <parameter free="1" max="-0.5" min="-5.0" name="Index" scale="1.0" value="-2.0"/>
      <parameter free="0" max="500000.0" min="20.0" name="Scale" scale="1.0" value="$EREF"/>
    </spectrum>
EOF
elif test "$MODEL" == "LP"
then
  cat <<EOF
<!-- point source units are cm^-2 s^-1 MeV^-1 -->
    <spectrum type="LogParabola">
      <parameter free="1" max="1000.0" min="0.001" name="norm" scale="1e-12" value="1.0"/>
      <parameter free="1" max="10" min="0" name="alpha" scale="1.0" value="2.0"/>
      <parameter free="0" max="500000.0" min="20.0" name="Eb" scale="1.0" value="$EREF"/>
      <parameter free="1" max="10" min="-10" name="beta" scale="1.0" value="0.0"/>
    </spectrum>
EOF
else
  cat <<EOF
<!-- point source units are cm^-2 s^-1 -->
    <spectrum type="PowerLaw2">
      <parameter free="1" max="10000.0" min="1e-05" name="Integral" scale="1e-09" value="2.0"/>
      <parameter free="1" max="-0.5" min="-5.0" name="Index" scale="1.0" value="-2.0"/>
      <parameter free="0" max="500000.0" min="20.0" name="LowerLimit" scale="1.0" value="$EMIN"/>
      <parameter free="0" max="500000.0" min="20.0" name="UpperLimit" scale="1.0" value="$EMAX"/>
    </spectrum>
EOF
fi

cat <<EOF
    <spatialModel type="SkyDirFunction">
      <parameter free="0" max="360.0" min="-360.0" name="RA" scale="1.0" value="$RA"/>
      <parameter free="0" max="90.0" min="-90.0" name="DEC" scale="1.0" value="$DEC"/>
    </spatialModel>
  </source>
EOF

# CATALOG SOURCES *************************************************************

if test "$CATALOG" \!= "none"
then
  if test `echo "$R_OUTER>$R_FROZEN" | bc` == "1"
  then
    ro=$R_FROZEN
  else
    ro=$R_OUTER
  fi
  echo "<!-- Sources from $CATALOG with free spectra (region: $REGION, $R_INNER, $ro) -->"
  catalog $R_INNER $ro 1 $RMODE
  echo "<!-- Sources from $CATALOG with frozen spectra (region: $REGION, $R_OUTER, $R_FROZEN) -->"
  catalog $R_FROZEN $R_OUTER 0 $RMODE
fi

cat <<EOF
</source_library>
EOF
