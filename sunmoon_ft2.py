#!/bin/env python

# sunmoon_ft2.py - Calculate apparent RA and Dec of Sun and Moon correcting
#                  for parallax of spacecraft in latter case
# Stephen Fegan - sfegan@llr.in2p3.fr - June 2011
# $Id: sunmoon_ft2.py 3426 2011-12-02 12:37:33Z sfegan $

import ephem
import pyfits
import sys
import math

def d2r(x): return x/180.0*math.pi
def r2d(x): return x/math.pi*180.0

if(len(sys.argv) < 1):
    print "Usage: %s FT2file",sys.argv[0]
    sys.exit(1)

# Open FITS file and read data into vectors
fits=pyfits.open(sys.argv[1])
data=fits['SC_DATA'].data
head=fits['SC_DATA'].header

sun = ephem.Sun()
moon = ephem.Moon()

for i in range(0, len(data), 10):
    t = 0.5*(data[i]['START']+data[i]['STOP'])
    r = data[i]['SC_POSITION']
    
    t_mjd = t/86400 + 51910
    t_djd = t_mjd + ( 2400000.5 - 2415020.0 )
    d = ephem.Date(t_djd)
    sun.compute(d)
    moon.compute(d)
    
    mr = moon.earth_distance * ephem.meters_per_au
    mz = mr*math.sin(moon.a_dec)
    mx = mr*math.cos(moon.a_dec)*math.cos(moon.a_ra)
    my = mr*math.cos(moon.a_dec)*math.sin(moon.a_ra)
    
    dx = mx - r[0]
    dy = my - r[1]
    dz = mz - r[2]
    
    mpd = math.atan2(dz,math.sqrt(dx*dx+dy*dy))
    mpr = math.fmod(math.atan2(dy,dx)+2.0*math.pi,2.0*math.pi)
    
    print data[i]['START'], t_mjd, \
        r2d(sun.a_ra), r2d(sun.a_dec), \
        r2d(mpr), r2d(mpd), \
        r2d(moon.a_ra), r2d(moon.a_dec), \
        r2d(math.acos((mx*dx+my*dy+mz*dz)/mr/math.sqrt(dx*dx+dy*dy+dz*dz)))
