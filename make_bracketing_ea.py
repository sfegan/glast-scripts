#!/usr/bin/env python

# make_bracketing_ea.py - modify the EA IRFs
# Stephen Fegan - sfegan@llr.in2p3.fr - 2011-02-10
# $Id$

import pyfits, sys, math, glob, re
import array
import numpy

def usage(fnkeys,Ed,K,errkeys):
    fnkeys.sort()
    print """
Usage: %s input.fits output.fits fntype [central_energy=%g] [K=%g] [Err]

where fntype describes the systematic error function to apply, which
must be one of:

 %s

The "central_energy" option gives the energy (in MeV) at which the 
transition between negative and positive systematic error occurs
in the study of the systematics on spectral index. The "K" option
specifies the smoothness of the transition - larger values give
smoother transitions. The "Err" option specifies which base systematic
error function to use, valid choices are:

  %s

If no value is given for "Err" then the program trys to determine
based on the name of the IRF files.

For spectral studies, to use the smoothed step function set "fntype"
to "indexhard" or "indexsoft", with the "central_energy" set to the
decorrelation energy of the source obtained with the unmodified
IRFs. Set "K" to %g (the default).

To use the traditional linear function (as per Phillipe's original
presentation), set "fntype" to "linearhard" or "linearsoft", and set
"central_energy" to 1000 and "K" to 1.0 to get a linear ramp between
100MeV and 10GeV (i.e. centered on 1000 with 1.0 decades below and
above).

The program outputs to STDOUT a table of five columns, with the energy,
unmodified effective area, systematic error, modulating function, and
modified effective area, which can be used for diagnostic purposes.

For example:

  %s aeff_P6_V11_DIFFUSE_front.fits aeff_P6_V11_DIFFUSE_indexhard_1200_front.fits indexhard 1200 > ea_indexhard_1200_front.dat

will make a bracketing effective area IRF for the \"indexhard\" function
with a transition at 1.2GeV, using the P6V11 IRFs as a baseline.

To use these in an analysis you would need to do the same thing for the 
back IRFs and then copy the \"edisp\" and \"psf\" files to have the same 
names, so that the directory contained:

  aeff_P6_V11_DIFFUSE_indexhard_1200_front.fits
  aeff_P6_V11_DIFFUSE_indexhard_1200_back.fits
  edisp_P6_V11_DIFFUSE_indexhard_1200_front.fits
  edisp_P6_V11_DIFFUSE_indexhard_1200_back.fits
  psf_P6_V11_DIFFUSE_indexhard_1200_front.fits
  psf_P6_V11_DIFFUSE_indexhard_1200_back.fits

This would make a complete set of IRFs with the name:

  \"P6_V11_DIFFUSE_indexhard_1200\"

which you could use in ST by setting the CUSTOM_IRF_NAMES and 
CUSTOM_IRF_DIR variables appropriately.
"""\
        %(sys.argv[0],Ed,K,", ".join(map(lambda(x): str(x), fnkeys)),", ".join(map(lambda(x): str(x), errkeys)),K,sys.argv[0])
    sys.exit(1)
    pass

# Define systematic error function
all_syst = dict(Pass6 = [ [ 2.00, 0.10 ], [ 2.75, 0.05 ], [ 4.00, 0.20 ] ],
                Pass7 = [ [ 2.00, 0.10 ], [ 2.75, 0.05 ], [ 4.00, 0.10 ] ]);
def_syst = 'Pass7'
use_syst = None

# Default parameters and function types available
Ed = 1000
K  = 0.13
fns = dict(fluxlo     = lambda(x): 1.0,
           fluxhi     = lambda(x): -1.0,
           indexsoft  = lambda(x): math.tanh(math.log10(x/Ed)/K),
           indexhard  = lambda(x): -math.tanh(math.log10(x/Ed)/K),
           linearsoft = lambda(x): min(1.0,max(-1.0,math.log10(x/Ed)/K)),
           linearhard = lambda(x): min(1.0,max(-1.0,-math.log10(x/Ed)/K)))

if(len(sys.argv) < 4):
    print "Need at least 3 arguments"
    usage(fns.keys(),Ed,K,all_syst.keys())

# Set function type selected and options Ed and K
fn=sys.argv[3]
if not fn in fns.keys():
    print "Unrecognised function type: \"%s\""%fn
    usage(fns.keys(),Ed,K)
fn = fns[fn]

if(len(sys.argv)>4):
    Ed = float(sys.argv[4])

if(len(sys.argv)>5):
    K = float(sys.argv[5])

if(len(sys.argv)>6):
    use_syst = sys.argv[6]

# Try to determine what version of the relative systematic error to use
if use_syst == None:
    use_syst = def_syst
    if re.search("P6_v11", sys.argv[1]): use_syst = 'Pass6'
    if re.search("P6_v3", sys.argv[1]): use_syst = 'Pass6'
    if re.search("p6_v3", sys.argv[1]): use_syst = 'Pass6'

sys.stderr.write("Using \"%s\" systematic error function:\n"%use_syst);
syst=all_syst[use_syst]

for icp in syst:
    E = "%.1f MeV"%(math.pow(10.0,icp[0]));
    if icp[0]>=3: E = "%.1f GeV"%(math.pow(10.0,icp[0]-3));
    sys.stderr.write("  %.1f%% at %s\n"%(100.0*icp[1],E))

# Open FITS file and read data into vectors
fits=pyfits.open(sys.argv[1])
data=fits[1].data[0]
head=fits[1].header

elo=data[0]
ehi=data[1]
zlo=data[2]
zhi=data[3]
aeff=data[4]

# Construct error function vector for interpolation
errx = [ math.log10(elo[0]) ]
erry = [ syst[0][1] ]
for isyst in syst:
    errx.append(isyst[0])
    erry.append(isyst[1])
errx.append(math.log10(ehi[-1]))
erry.append(syst[-1][1])

# Scale the effective area curves
for i in range(len(elo)*len(zlo)):
    ie = i%len(elo)
    iz = i/len(elo)
    ee = math.sqrt(elo[ie]*ehi[ie])
    log10ee = math.log10(ee)
    err = numpy.interp(log10ee, errx, erry)
    f = fn(ee)
    try:
        aeffi = aeff[iz][ie]
    except:
        aeffi = aeff[i]
    ae = aeffi * (1 + err*f)
    if(iz == len(zlo)-1):
        print ee,aeffi,err,f,ae
    try:
        aeff[iz][ie] = ae
    except:
        aeff[i] = ae

# Write the data to the new FITS file
data[4][:]=aeff
fits[1].data[0]=data
fits.writeto(sys.argv[2])
