#!/bin/bash

# copy_slac.sh - copy new data files from SLAC and run diffrsp on them
# Stephen Fegan - sfegan@llr.in2p3.fr - 2008-10-15
# $Id$

if test "$ECHO" == ""; then ECHO= ; fi

$ECHO cp -v ~/SLAC/gev/gll_pt_* SPACECRAFT
$ECHO cp -v ~/SLAC/gev/gll_ph_* CTBCLASSLEVEL2

allph=`ls ~/SLAC/gev/gll_ph_*`

for f in $allph
do
  fb=`basename $f`
  rm -f CTBCLASSLEVEL3/$fb
  $ECHO fcopy CTBCLASSLEVEL2/$fb'[CTBCLASSLEVEL>2]' CTBCLASSLEVEL3/$fb
done

echo `/bin/pwd`/CTBCLASSLEVEL2_DIFFRSP/*.fit | xargs -n1 echo > FT1_CTB2.dat
echo `/bin/pwd`/CTBCLASSLEVEL3_DIFFRSP/*.fit | xargs -n1 echo > FT1_CTB3.dat
echo `/bin/pwd`/CTBCLASSLEVEL2/*.fit | xargs -n1 echo > FT1_CTB2_NODIFFRSP.dat
echo `/bin/pwd`/CTBCLASSLEVEL3/*.fit | xargs -n1 echo > FT1_CTB3_NODIFFRSP.dat
echo `/bin/pwd`/SPACECRAFT/*.fit | xargs -n1 echo > FT2.dat

# nft2=`wc FT2.dat | awk '{print $1}'`
#
# ift2=0
# rm -f FT2_many.dat
# while test $ift2 -lt $nft2
# do
#   jft2=$((ift2+500))
#   awk "NR>$ift2&&NR<=$jft2" FT2.dat > FT2_$ift2.dat
#   $ECHO fmerge @FT2_$ift2.dat \!FT2_$ift2.fit -
#   echo `pwd`/FT2_$ift2.fit >> FT2_many.dat
#   ift2=$jft2
# done
# 
# $ECHO fmerge @FT2_many.dat \!FT2.fits -

$ECHO ftmerge @FT2.dat \!FT2.fits

for f in $allph
do
  fb=`basename $f`
  $ECHO qdiffrsp.sh `/bin/pwd`/CTBCLASSLEVEL3/$fb `/bin/pwd`/CTBCLASSLEVEL3_DIFFRSP P6_V1_DIFFUSE
done

for f in $allph
do
  fb=`basename $f`
  $ECHO qdiffrsp.sh `/bin/pwd`/CTBCLASSLEVEL2/$fb `/bin/pwd`/CTBCLASSLEVEL2_DIFFRSP P6_V1_SOURCE
done

