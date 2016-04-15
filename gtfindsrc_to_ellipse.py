# -*-mode:python; mode:font-lock;-*-
"""
@file gtfindsrc_to_ellipse.py

@brief Function to calculate r68 ellipse from o/p of gtfindsrc

@author Stephen Fegan <sfegan@llr.in2p3.fr>

$Id: gtfindsrc_to_ellipse.py 2003 2010-07-28 10:48:28Z sfegan $
"""

import math
import numpy

def fit_paraboloid(x,y,z):
    # Use method of D. Eberly (see section 9 in document below)
    # http://www.geometrictools.com/Documentation/LeastSquaresFitting.pdf

    if(len(x)!=len(y) or len(x)!=len(z)):
        print "Length of x, y and z vectors must be same"
        return None

    A=numpy.array(0)
    A.resize(6,6)
    B=numpy.array(0)
    B.resize(6,1)

    for i in range(0,len(x)):
        Q = numpy.matrix([x[i]*x[i],x[i]*y[i],y[i]*y[i],x[i],y[i],1]).T
        A = A + Q*Q.T
        B = B + z[i]*Q
        pass

    p = numpy.linalg.solve(A,B)
    return [p[0,0],p[1,0],p[2,0],p[3,0],p[4,0],p[5,0]]

def rotate(ra, dec, phi, theta, psi):
    sf=math.sin(phi)
    cf=math.cos(phi)
    st=math.sin(theta)
    ct=math.cos(theta)
    sp=math.sin(psi)
    cp=math.cos(psi)
    
    r=numpy.matrix([math.cos(dec)*math.sin(ra), math.cos(dec)*math.cos(ra), math.sin(dec)]).T
    
    T=numpy.matrix([[cf,sf,0],[-sf,cf,0],[0,0,1]])\
        *numpy.matrix([[1,0,0],[0,ct,-st],[0,st,ct]])\
        *numpy.matrix([[cp,sp,0],[-sp,cp,0],[0,0,1]]);
    r=T*r;

    dec=math.atan(r[2]/math.sqrt(r[0]*r[0]+r[1]*r[1]))
    ra=math.atan2(r[0],r[1])
    return ra,dec

def calc_ellipse(filename, verbose=False,
                 delta_logL_cut=None, delta_logL_radius = 2.71/2):
    f = open(filename, 'r')
    lines = f.readlines()

    ra   = []
    dec  = []
    logL = []

    for l in lines[0:-3]:
        bits = l.split();
        ra.append(float(bits[0])/180.0*math.pi)
        dec.append(float(bits[1])/180.0*math.pi)
        logL.append(float(bits[2]))
        pass

    ra0   = ra[-1]
    dec0  = dec[-1]
    logL0 = logL[-1]

    x=[]
    y=[]
    z=[]

    if verbose:
        print "Cutting points with delta LogL >",delta_logL_cut
    
    for i in range(0,len(ra)):
        if delta_logL_cut != None and logL[i]>logL0+delta_logL_cut:
            continue
        [_x, _y] = rotate(ra[i],dec[i],0,-dec0,-ra0)
        x.append(_x/math.pi*180.0)
        y.append(_y/math.pi*180.0)
        z.append(logL[i])
        if verbose:
            print x[-1], y[-1], z[-1]
        pass

    if verbose:
        print "Calculating paraboloid from %d point(s)"%len(x)

    p = fit_paraboloid(x,y,z)
    A = numpy.matrix([[p[0],p[1]/2],[p[1]/2,p[2]]])
    [l,v] = numpy.linalg.eig(A)
#    print l
#    print v
    
    ima = 0
    imi  =1
    if(l[0]>l[1]): 
        ima=1
        imi=0

    r1 = math.sqrt(delta_logL_radius/l[ima])
    r2 = math.sqrt(delta_logL_radius/l[imi])
    xc = (p[1]*p[4]-2*p[2]*p[3])/(4*p[0]*p[2]-p[1]*p[1])
    yc = (p[1]*p[3]-2*p[0]*p[4])/(4*p[0]*p[2]-p[1]*p[1])
    th = math.atan(v[1,ima]/v[0,ima])/math.pi*180.0

    [rac, decc] = rotate(xc/180.0*math.pi,yc/180.0*math.pi,ra0,dec0,0)
    rac *= 180.0/math.pi
    decc *= 180.0/math.pi

    return [r1,r2,th,xc,yc,rac,decc]

if __name__ == "__main__":
    import getopt
    import sys
    import os
    def usage(defcut, defprob, deflogl, exitcode = 0):
        progname = os.path.basename(sys.argv[0])
        print """usage: %s [options] gtfindsrc_output_file

Compute uncertainty ellipse from output of gtfindsrc.

General options:

-h,--help        print this message.

-v               be verbose about doing operations.

-c,--cut X       remove values above a threshold log Likelihood from fit
                 [default: %g].

-p,--prob X      specify the radius of the ellipse in terms of a probability.
                 Only accept 0.68 or 0.95 (since we don't want to use scipy).
                 Use --loglike to specify other values. [default: %g].

-l,--loglike X   specify the radius of the ellipse in terms of a change in
                 log Likelihood from the minimum value [default: %g].
"""%(progname,defcut,defprob,deflogl)
        sys.exit(exitcode)


    try:
        optspec = ( 'help', 'cut=', 'prob=', 'loglike=')
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'hvc:p:l:', optspec)
    except getopt.GetoptError, err:
        print err
        smallHelp(0)

    defcut     = 2.0
    defprob    = 0.68
    deflogl    = 2.28
    verbose    = False

    cut        = defcut
    logl       = deflogl
    
    for o, a in opts:
        if o in ('-h', '--help'):
            usage(defcut,defprob,deflogl)
        elif o in ('-v'):
            verbose = True
        elif o in ('-c', '--cut'):
            cut = float(a)
        elif o in ('-l', '--loglike'):
             logl= float(a)
        elif o in ('-p', '--prob'):
            prob = float(a)
            if a==0.68:
                logl = 2.28
            elif a==0.95:
                logl = 5.99
            else:
                print "Probability can only be 0.68 or 0.95"
                sys.exit(0)

    if len(args)<1:
        print "Must specify file name!"
        usage(defcut,defprob,deflogl)
    
    file_name = args[0]

    E=calc_ellipse(file_name, verbose=verbose,
                   delta_logL_cut=cut, delta_logL_radius=logl/2.0)

    print "R major: %9.5f deg"%E[0]
    print "R minor: %9.5f deg"%E[1]
    print "Theta:   %9.5f deg"%E[2]
    print "RA:      %9.5f deg (X=%.8f)"%(E[5],E[3])
    print "Dec:     %9.5f deg (Y=%.8f)"%(E[6],E[4])
