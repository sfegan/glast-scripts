#!/bin/bash

if test "$RUN" == ""
then
  RUN=""
fi

NAME=$1
IRF=$2
FT2=$3

if test "$IRF" == ""
then
  IRF=P7SOURCE_V6
fi

if test "$FT2" == ""
then
  FT2=/sps/hep/glast/data/FSSCWeeklyData/FT2.fits
fi

#
# GTSELECT : Separate front & back events
#
CMD="gtselect convtype=0 infile=${NAME}_ev_roi.fits outfile=${NAME}_ev_roi_F.fits ra=INDEF dec=INDEF rad=INDEF tmin=INDEF tmax=INDEF emin=0 emax=1E100 zmax=180"
echo $CMD
$RUN $CMD

CMD="gtselect convtype=1 infile=${NAME}_ev_roi.fits outfile=${NAME}_ev_roi_B.fits ra=INDEF dec=INDEF rad=INDEF tmin=INDEF tmax=INDEF emin=0 emax=1E100 zmax=180"
echo $CMD
$RUN $CMD

#
# GDBIN: Make the counts cube
#
for v in NAXIS1 NAXIS2 NAXIS3 CRVAL1 CRVAL2 CRVAL3 CDELT2 CDELT3
do
    declare ${v}=`ftlist ${NAME}_ccube.fits'[0]' K include=$v | cut -b 10-30 | sed -e 's/^ *//;'`
done
EMAX=`awk -v edel=$CDELT3 -v e0=$CRVAL3 -v ne=$NAXIS3 'BEGIN{print exp((log(e0+edel)-log(e0))*ne+log(e0))}' /dev/null`

CMD="gtbin evfile=${NAME}_ev_roi_F.fits scfile=${FT2} outfile=${NAME}_ccube_F.fits algorithm=CCUBE nxpix=${NAXIS1} nypix=${NAXIS2} binsz=${CDELT2} coordsys=CEL xref=${CRVAL1} yref=${CRVAL2} axisrot=0 proj=STG ebinalg=LOG emin=${CRVAL3} emax=${EMAX} enumbins=${NAXIS3}"
echo $CMD
$RUN $CMD
CMD="gtbin evfile=${NAME}_ev_roi_B.fits scfile=${FT2} outfile=${NAME}_ccube_B.fits algorithm=CCUBE nxpix=${NAXIS1} nypix=${NAXIS2} binsz=${CDELT2} coordsys=CEL xref=${CRVAL1} yref=${CRVAL2} axisrot=0 proj=STG ebinalg=LOG emin=${CRVAL3} emax=${EMAX} enumbins=${NAXIS3}"
echo $CMD
$RUN $CMD

#
# GDBIN: Make the extended counts cube
#
for v in NAXIS1 NAXIS2 NAXIS3 CRVAL1 CRVAL2 CRVAL3 CDELT2 CDELT3
do
    declare ${v}=`ftlist ${NAME}_extended_ccube.fits'[0]' K include=$v | cut -b 10-30 | sed -e 's/^ *//;'`
done
EMAX=`awk -v edel=$CDELT3 -v e0=$CRVAL3 -v ne=$NAXIS3 'BEGIN{print exp((log(e0+edel)-log(e0))*ne+log(e0))}' /dev/null`

CMD="gtbin evfile=${NAME}_ev_roi_F.fits scfile=${FT2} outfile=${NAME}_extended_ccube_F.fits algorithm=CCUBE nxpix=${NAXIS1} nypix=${NAXIS2} binsz=${CDELT2} coordsys=CEL xref=${CRVAL1} yref=${CRVAL2} axisrot=0 proj=STG ebinalg=LOG emin=${CRVAL3} emax=${EMAX} enumbins=${NAXIS3}"
echo $CMD
$RUN $CMD
CMD="gtbin evfile=${NAME}_ev_roi_B.fits scfile=${FT2} outfile=${NAME}_extended_ccube_B.fits algorithm=CCUBE nxpix=${NAXIS1} nypix=${NAXIS2} binsz=${CDELT2} coordsys=CEL xref=${CRVAL1} yref=${CRVAL2} axisrot=0 proj=STG ebinalg=LOG emin=${CRVAL3} emax=${EMAX} enumbins=${NAXIS3}"
echo $CMD
$RUN $CMD

#
# GTEXPMAPCUBE2 - Make the exposure map
#
CMD="gtexpcube2 infile=${NAME}_expCube.fits cmap=${NAME}_extended_ccube_F.fits outfile=${NAME}_binExpMap_F.fits irfs=${IRF}::FRONT bincalc=EDGE"
echo $CMD
$RUN $CMD
CMD="gtexpcube2 infile=${NAME}_expCube.fits cmap=${NAME}_extended_ccube_B.fits outfile=${NAME}_binExpMap_B.fits irfs=${IRF}::BACK bincalc=EDGE"
echo $CMD
$RUN $CMD

#
# GTSRCMAPS - Make the source maps
#
CMD="gtsrcmaps scfile=${FT2} expcube=${NAME}_expCube.fits cmap=${NAME}_ccube_F.fits srcmdl=${NAME}_model.xml bexpmap=${NAME}_binExpMap_F.fits outfile=${NAME}_preSrcMaps_F.fits irfs=${IRF}::FRONT"
echo $CMD
$RUN $CMD
CMD="gtsrcmaps scfile=${FT2} expcube=${NAME}_expCube.fits cmap=${NAME}_ccube_B.fits srcmdl=${NAME}_model.xml bexpmap=${NAME}_binExpMap_B.fits outfile=${NAME}_preSrcMaps_B.fits irfs=${IRF}::BACK"
echo $CMD
$RUN $CMD
