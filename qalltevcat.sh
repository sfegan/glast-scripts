#!/bin/bash

# qalltevcat.sh - queue GLAST analysis runs for all TeVCat sources at ccin2p3
# Stephen Fegan - sfegan@llr.in2p3.fr - 2008-10-22
# $Id: qalltevcat.sh 1988 2010-07-21 11:59:29Z sfegan $

if test "$1" == ""
then
  CATALOG=/afs/in2p3.fr/home/s/sfegan/catalogs/tevcat.txt
else 
  CATALOG=$1
fi

shift

if test "$ECHO" == ""
then
  ECHO=
fi

if test "$DIRPREFIX" == ""
then
  DIRPREFIX=""
fi

for details in `sed -e 's/ /_/g' $CATALOG`
do 
  UNSANITISED_NAME=`echo $details | cut -d, -f1`
  NAME=`sanitize_name.sh "$UNSANITISED_NAME"`
  RA=`echo $details | cut -d, -f8`
  DEC=`echo $details | cut -d, -f9`

  $ECHO mkdir ${DIRPREFIX}${NAME}
  $ECHO qanalyze.sh $RA $DEC $NAME ${DIRPREFIX}${NAME} "$@"
done
