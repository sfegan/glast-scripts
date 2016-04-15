#!/usr/bin/python

# epivot.py - calculate the pivot energy from PL2 fit parameters
# See: http://tinyurl.com/epivot for further details
# Stephen Fegan - sfegan@llr.in2p3.fr - 2011-03-31
# $Id: epivot.py 2708 2011-04-01 11:39:13Z sfegan $

import math
import sys

if len(sys.argv) != 7:
    print """Usage %s K g CKg Cgg E1 E2

Calculate the pivot energy from the parameters of a PowerLaw2 and
elements of the error matrix. See Jean Ballet's memo:

  http://tinyurl.com/epivot for further details

for futher details. This program implements Eqns 7 and 7bis.

Required parameters:

  K   - Integral flux from PL2
  g   - Spectral index (defined in the sense of the ST, i.e. less than zero)
  CKg - Covarience between K and g
  Cgg - Varience of g
  E1  - Low energy bound of PL2 energy range
  E2  - High energy bound of PL2 energy range"""%sys.argv[0]
    sys.exit(1)

K   = float(sys.argv[1])
g   = float(sys.argv[2])
CKg = float(sys.argv[3])
Cgg = float(sys.argv[4])
E1  = float(sys.argv[5])
E2  = float(sys.argv[6])

if g == -1:
    loge = (math.log(E1)+math.log(E2))/2-CKg/K/Cgg;
else:
    epsilon=(E2/E1)**(1+g);
    loge=(math.log(E1)-epsilon*math.log(E2))/(1-epsilon)-1/(g+1)-CKg/K/Cgg;

e=math.exp(loge);
print e
