#!/usr/bin/python
# -*-mode:python; mode:font-lock;-*-
"""
@file GaussFlare.py

@brief Class to calculate light curves.

@author Stephen Fegan <sfegan@llr.in2p3.fr>

@date 2010-06-22

$Id: GaussFlare.py 2003 2010-07-28 10:48:28Z sfegan $
"""

import glob
import socket
import os
import struct
import os.path
import math
import pickle
import numpy
import scipy.special
import sys
import UnbinnedAnalysis
import IntegralUpperLimit

class GaussFlare:
    """Class to calculate light curves and variability indexes."""
    def __init__(self, toffset=0,
                 srcName=None, ft2=None, irfs=None, model=None,
                 optimizer="Minuit", verbosity=0):
        self.ver = "$Id: GaussFlare.py 2003 2010-07-28 10:48:28Z sfegan $"
        self.lc = []
        if(srcName == None):
            return
        self.srcName = srcName
        if model != None:
            self.model = model
        else:
            self.model = srcName + "_fitmodel.xml"
        self.ft2 = ft2
        self.irfs = irfs
        self.optimizer = optimizer
        self.obsfiles = []
        self.toffset = toffset
        self.verbosity = verbosity

    def globStandardObsDir(self, directory_glob, ft2=None, irfs=None):
        directories = glob.glob(directory_glob)
        directories.sort()
        for d in directories:
            if os.path.isdir(d):
                self.addStandardObsDir(d, ft2, irfs)

    def addStandardObsDir(self, directory, ft2=None, irfs=None):
        prefix = directory+"/"+self.srcName
        ft1 = prefix + "_ev_roi.fits"
        emap = prefix + "_expMap.fits"
        ecube = prefix + "_expCube.fits"
        self.addObs(ft1, emap, ecube, ft2, irfs)

    def addObs(self, ft1, emap, ecube, ft2=None, irfs=None):
        if ft2 != None: _ft2 = ft2
        else: _ft2 = self.ft2
        if irfs != None: _irfs = irfs
        else: _irfs = self.irfs
        if not os.path.isfile(ft1):
            raise IOError('FT1 file not found: '+ft1);
        if not os.path.isfile(_ft2):
            raise IOError('FT2 file not found: '+_ft2);
        if not os.path.isfile(emap):
            raise IOError('ExpMap not found: '+emap);
        if not os.path.isfile(ecube):
            raise IOError('ExpCube not found: '+ecube);
        obsfiles = dict(ft1       = ft1,
                        ft2       = _ft2,
                        emap      = emap,
                        ecube     = ecube,
                        irfs      = _irfs)
        self.obsfiles.append(obsfiles)
        
    def loadAllObs(self, emin=100, emax=100000):
        verbosity = self.verbosity
        self.objs = []
        for f in self.obsfiles:
            if verbosity:
                print 'Loading observation:',f['ft1']

            obs = UnbinnedAnalysis.UnbinnedObs(f['ft1'], f['ft2'], f['emap'],
                                               f['ecube'], f['irfs'])
            like = UnbinnedAnalysis.UnbinnedAnalysis(obs, srcModel=self.model,
                                                    optimizer=self.optimizer)
            like.tol = like.tol*0.01;

            t_min = obs.roiCuts().minTime()/86400+51910
            t_max = obs.roiCuts().maxTime()/86400+51910
            if verbosity > 1:
                print '- Time:',t_min,'to',t_max

            src = like[self.srcName]
            if src == None:
                raise NameError("No source \""+self.srcName+"\" in model "+
                                self.model)
            srcfreepar=like.freePars(self.srcName)
            srcnormpar=like.normPar(self.srcName)
            if not srcfreepar.empty():
                like.setFreeFlag(self.srcName, srcfreepar, 0)
                like.syncSrcParams(self.srcName)

            if verbosity > 1:
                print '- Original log Like:',like.logLike.value()

            if verbosity > 1:
                print '- Fixing spectral shape parameters'
            sync_name = ""
            for p in like.params():
                if sync_name != "" and sync_name != p.srcName:
                    like.syncSrcParams(sync_name)
                    sync_name = ""
                if(p.isFree() and p.srcName!=self.srcName and
                   p.getName()!=like.normPar(p.srcName).getName()):
                    if verbosity > 2:
                        print '-- '+p.srcName+'.'+p.getName()
                    p.setFree(False)
                    sync_name = p.srcName
            if sync_name != "" and sync_name != p.srcName:
                like.syncSrcParams(sync_name)
                sync_name = ""
                
            obj = dict(obs              = obs,
                       like             = like,
                       t_min            = t_min,
                       t_max            = t_max,
                       srcfreepar       = srcfreepar,
                       srcnormpar       = srcnormpar)
            
            self.objs.append(obj)

    def calc(self, F0, FA, t0, sigma):
        logL = 0
        for obj in self.objs:
            # ------------------------------ FIT -----------------------------
            
            tmin = obj['t_min'] - t0 - self.toffset;
            tmax = obj['t_max'] - t0 - self.toffset;
            flux = F0 + FA*sigma*math.sqrt(numpy.pi/2)/(tmax-tmin)\
                *(scipy.special.erf(tmax/sigma/math.sqrt(2))-
                  scipy.special.erf(tmin/sigma/math.sqrt(2)))
#            flux = F0 + FA*math.exp(-0.5*(t-t0)**2/sigma**2);
            if self.verbosity > 1:
                print '- Fit - Flux of',self.srcName,'=',flux
            obj['srcnormpar'].setValue(flux)
            obj['like'].syncSrcParams(self.srcName)                    
            obj['like'].fit(max(self.verbosity-3, 0))

            if self.verbosity > 1:
                print '- Post-fit log Like:',obj['like'].logLike.value()
            logL += obj['like'].logLike.value()
            pass
        if self.verbosity > 1:
            print '- Total logL',-logL
        return -logL

if __name__ == "__main__":
    import getopt
    def smallHelp(exitcode = 0):
        print "See '%s -h' for more help"%os.path.basename(sys.argv[0])
        sys.exit(exitcode)
    
    def usage(defirf, defft2, exitcode = 0):
        progname = os.path.basename(sys.argv[0])
        print """usage: %s --server [options] socket source_name directory [directory...]
       %s --client socket F0 FA t0 sigma

Compute summed likelihood of Gaussian flux model in lightcurves of 
Fermi data.

General options:

-h,--help        print this message.

--v              be verbose about doing operations.
--vv             be very verbose.

Compute mode options:

--toffset X      specify the origin of the time parameter [MJD, default 0].

--irf X          specify the IRFs to use [default: %s].

--ft2 X          specify the FT2 file
                 [default: %s].

--fitmodel X     specify filename of XML model from global fit
                 [default: source_name_fitmodel.xml].
"""%(progname,defirf,defft2)
        sys.exit(exitcode)


    try:
        optspec = ( 'help', 'v', 'vv', 'client', 'server',
                    'ft2=', 'irf=', 'toffset=', 'fitmodel=' )
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'hv:', optspec)
    except getopt.GetoptError, err:
        print err
        smallHelp(0)

    mode       = "server"
    defirf     = 'P6_V3_DIFFUSE'
    defft2     = '/sps/hep/glast/users/sfegan/newdata/FT2.fits'

    verbose = 0
    srcmodel = None
    toffset = 0

    irf     = defirf
    ft2     = defft2
    
    for o, a in opts:
        if o in ('-h', '--help'):
            usage(defirf,defft2)
        elif o in ('-o', '--output'):
            output = a
        elif o in ('-v', '--v'):
            verbose = 1
        elif o in ('--vv'):
            verbose = 2
        elif o in ('--vvv'):
            verbose = 3
        elif o in ('--irf'):
            irf = a
        elif o in ('--ft2'):
            ft2 = a
        elif o in ('--srcmodel'):
            src_model = a
        elif o in ('--toffset'):
            toffset = float(a)
        elif o in ('--client'):
            mode = "client"
        elif o in ('--server'):
            mode = "server"
    
    if mode == "client":
        if len(args)<5:
            print "Must specify socket name and 4 model parameters!"
            smallHelp()
        socket_fn = args[0]
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(socket_fn)
        F0 = float(args[1])
        FA = float(args[2])
        t0 = float(args[3])
        s = float(args[4])
        data = struct.pack('dddd',F0,FA,t0,s)
        sock.send(data)
        logL = 0.0
        data = struct.pack('d',logL)
        data = sock.recv(len(data))
        logL = struct.unpack('d',data)
        print "%.17e"%(logL[0])
    else:
        if len(args)<3:
            print "Must specify socket name, source name and at least one directory!"
            smallHelp()
        socket_fn = args[0]
        source_name = args[1]        
        args=args[2:]
        lc=GaussFlare(toffset, verbosity=verbose,
                      srcName=source_name,ft2=ft2,irfs=irf,model=srcmodel)
        for d in args:
            lc.globStandardObsDir(d)
        lc.loadAllObs()
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            os.remove(socket_fn)
        except OSError:
            pass
        sock.bind(socket_fn)
        sock.listen(1)
        if verbose:
            print "Listening on",socket_fn
        while 1:
            conn, addr = sock.accept()
            F0 = 0.0
            FA = 0.0
            t0 = 0.0
            s = 0.0
            data = struct.pack('dddd',F0,FA,t0,s)
            data = conn.recv(len(data))
            F0, FA, t0, s = struct.unpack('dddd',data)
            if verbose:
                print "Request for",F0,FA,t0,s
            logL=lc.calc(F0,FA,t0,s)
            data = struct.pack('d',logL)
            conn.send(data)
