#!/usr/bin/python
# -*-mode:python; mode:font-lock;-*-
"""
@file Spectrum.py

@brief Class to calculate spectra.

@author Stephen Fegan <sfegan@llr.in2p3.fr>

@date 2010-06-23

$Id$
"""

import sys
import glob
import os.path
import math
import pickle
import scipy.stats
import UnbinnedAnalysis
import BinnedAnalysis
import SummedLikelihood
import IntegralUpperLimit

class Spectrum:
    """Class to calculate spectra."""
    def __init__(self, srcName=None, ft2=None, irfs=None, 
                 model=None, optimizer="Minuit"):
        self.ver = "$Id$"
        self.spectra = []
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

    def globStandardObsDir(self, directory_glob, analysis='unbinned',
                           ft2=None, irfs=None):
        directories = glob.glob(directory_glob)
        directories.sort()
        for d in directories:
            self.addStandardObsDir(d, ft2, irfs, analysis)

    def addStandardObsDir(self, directory, ft2=None, irfs=None,
                          analysis='unbinned'):
        prefix = directory+"/"+self.srcName
        ecube = prefix + "_expCube.fits"
        if self.model.find('/'):
            model = self.model
        else:
            model = directory + "/" + self.model
        if analysis=='unbinned':
            ft1 = prefix + "_ev_roi.fits"
            emap = prefix + "_expMap.fits"
            self.addUnbinnedObs(ft1, emap, ecube, model, ft2, irfs)
        elif analysis=='binned':
            smaps = prefix + "_srcMaps.fits"
            bemap = prefix + "_binExpMap.fits"
            self.addBinnedObs(smaps, bemap, ecube, model, irfs)
        else:
            raise NameError("Unknown analysis type: \""+f['analysis']+
                            "\" for directory \""+directory+"\"")

    def addUnbinnedObs(self, ft1, emap, ecube, model, ft2=None, irfs=None):
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
        if not os.path.isfile(model):
            raise IOError('Model not found: '+model);
        obsfiles = dict(analysis  = 'unbinned',
                        ft1       = ft1,
                        ft2       = _ft2,
                        emap      = emap,
                        ecube     = ecube,
                        model     = model,
                        irfs      = _irfs)
        self.obsfiles.append(obsfiles)

    def addBinnedObs(self, smaps, bemap, ecube, model, irfs=None):
        if irfs != None: _irfs = irfs
        else: _irfs = self.irfs
        if not os.path.isfile(smaps):
            raise IOError('SourceMaps file not found: '+smaps);
        if not os.path.isfile(bemap):
            raise IOError('Binned ExpMap not found: '+bemap);
        if not os.path.isfile(ecube):
            raise IOError('ExpCube not found: '+ecube);
        if not os.path.isfile(model):
            raise IOError('Model not found: '+model);
        obsfiles = dict(analysis  = 'binned',
                        smaps     = smaps,
                        bemap     = bemap,
                        ecube     = ecube,
                        model     = model,
                        irfs      = _irfs)
        self.obsfiles.append(obsfiles)

    def loadUnbinnedObs(self, f, verbosity=0):
        if verbosity:
            print 'Loading unbinned observation:',f['ft1']
        obs = UnbinnedAnalysis.UnbinnedObs(eventFile=f['ft1'], scFile=f['ft2'],
                                           expMap=f['emap'],expCube=f['ecube'],
                                           irfs=f['irfs'])
        like = UnbinnedAnalysis.UnbinnedAnalysis(obs, srcModel=f['model'],
                                                 optimizer=self.optimizer)
        return [ obs, like ]

    def loadBinnedObs(self, f, verbosity=0):
        if verbosity:
            print 'Loading binned observation:',f['smaps']
        obs = BinnedAnalysis.BinnedObs(srcMaps=f['smaps'], expCube=f['ecube'], 
                                       binnedExpMap=f['bemap'], irfs=f['irfs'])
        like = BinnedAnalysis.BinnedAnalysis(obs, srcModel=f['model'],
                                             optimizer=self.optimizer)
        return [ obs, like ]

    def loadObs(self, f, verbosity=0):
        if f['analysis'] == 'unbinned':
            return self.loadUnbinnedObs(f, verbosity)
        elif f['analysis'] == 'binned':
            return self.loadBinnedObs(f, verbosity)
        else:
            raise NameError("Unknown analysis type: \""+f['analysis']+"\"")

    def processAllObs(self, fix_shape=True, delete_below_ts=None,
                      ul_flux_dflux=0,ul_chi2_ts=None, ul_bayes_ts=4.0,
                      ul_cl = 0.95, verbosity=0, ul_optimizer=None):
        for f in self.obsfiles:
            spect = dict()
            spect['config']=dict()
            spect['config']['fix_shape'] = fix_shape
            spect['config']['delete_below_ts'] = delete_below_ts
            spect['config']['ul_flux_dflux'] = ul_flux_dflux
            spect['config']['ul_chi2_ts'] = ul_chi2_ts
            spect['config']['ul_bayes_ts'] = ul_bayes_ts
            spect['config']['ul_cl'] = ul_cl
            spect['config']['files'] = f

            [ obs, like ] = self.loadObs(f,verbosity)

            spect['t_min'] = obs.roiCuts().minTime()
            spect['t_max'] = obs.roiCuts().maxTime()
            [emin, emax] = obs.roiCuts().getEnergyCuts()
            spect['e_min'] = emin
            spect['e_max'] = emax
            
            if verbosity > 1:
                print '- Time:',spect['t_min'],'to',spect['t_max']
                print '- Energy:',emin,'to',emax,'MeV'

            src = like[self.srcName]
            if src == None:
                raise NameError("No source \""+self.srcName+"\" in model "+
                                self.model)
            srcnormpar=like.normPar(self.srcName)

            spect['original']=dict()
            spect['original']['normpar_init_value'] = srcnormpar.getValue()
            spect['original']['normpar_name'] = srcnormpar.getName()
            spect['original']['flux'] = like[self.srcName].flux(emin, emax)
            spect['original']['logL'] = like.logLike.value()
            if verbosity > 1:
                print '- Original log Like:',spect['original']['logL']

            if fix_shape:
                if verbosity > 1:
                    print '- Fixing spectral shape parameters'
                sync_name = ""
                for p in like.params():
                    if sync_name != "" and sync_name != p.srcName:
                        like.syncSrcParams(sync_name)
                        sync_name = ""
                    if(p.isFree() and #p.srcName!=self.srcName and
                       p.getName()!=like.normPar(p.srcName).getName()):
                        if verbosity > 2:
                            print '-- '+p.srcName+'.'+p.getName()
                        p.setFree(False)
                        sync_name = p.srcName
                if sync_name != "" and sync_name != p.srcName:
                    like.syncSrcParams(sync_name)
                    sync_name = ""

            # ------------------------------ FIT ------------------------------

            if verbosity > 1:
                print '- Fit - starting'
            like.fit(max(verbosity-3, 0))

            spect['fit'] = dict()
            spect['fit']['logL'] = like.logLike.value()
            if verbosity > 1:
                print '- Fit - log Like:',spect['fit']['logL']

            if delete_below_ts:
                frozensrc = []
                if verbosity > 1:
                    print '- Deleting point sources with TS<'+str(delete_below_ts)
                deletesrc = []
                for s in like.sourceNames():
                    freepars = like.freePars(s)
                    if(s!=self.srcName and like[s].type == 'PointSource'
                       and len(freepars)>0):
                        ts = like.Ts(s)
                        if ts<delete_below_ts:
                            deletesrc.append(s)
                            if verbosity > 2:
                                print '--',s,'(TS='+str(ts)+')'
                if deletesrc:
                    for s in deletesrc:
                        like.deleteSource(s)
                    if verbosity > 1:
                        print '- Fit - refitting model'
                    like.fit(max(verbosity-3, 0))
                    spect['fit']['logL'] = like.logLike.value()
                    if verbosity > 1:
                        print '- Fit - log Like:',spect['fit']['logL']
                        
            spect['fit']['ts']=like.Ts(self.srcName)
            if verbosity > 1:
                print '- TS of %s: %f'%(self.srcName,spect['fit']['ts'])

            spect['fit']['flux']=like[self.srcName].flux(emin, emax)
            emid = math.sqrt(emin*emax)
            spect['fit']['e_mid']=emid
            # Note: be careful about the meaning here - it is the
            # differential flux in the middle of the energy bin, not a
            # flux error. This contradicts the meaning in 'flux_dflux' 
            spect['fit']['dflux'] = \
                like[self.srcName].flux(emid*(1-0.001),emid*(1+0.001))/(emid*0.002)
            spect['fit']['flux_dflux'] = \
                srcnormpar.getValue()/srcnormpar.error()
            pars = dict()
            for pn in like[self.srcName].funcs['Spectrum'].paramNames:
                p = like[self.srcName].funcs['Spectrum'].getParam(pn)
                pars[p.getName()] = dict(name      = p.getName(),
                                         value     = p.getTrueValue(),
                                         error     = p.error()*p.getScale(),
                                         free      = p.isFree())
            spect['fit']['pars'] = pars

            ul_type = None
            if ul_bayes_ts != None and spect['fit']['ts'] < ul_bayes_ts:
                ul_type = 'bayesian'
                [ul_flux, ul_results] = \
                    IntegralUpperLimit.calc_int(like,self.srcName,cl=ul_cl,
                                                skip_global_opt=True,
                                                verbosity = max(verbosity-2,0),
                                                emin=emin, emax=emax,
                                                profile_optimizer=ul_optimizer)
            elif ( ul_flux_dflux != None and \
                   spect['fit']['flux_dflux'] < ul_flux_dflux ) or \
                   ( ul_chi2_ts != None and spect['fit']['ts'] < ul_chi2_ts):
                ul_type = 'chi2'
                [ul_flux, ul_results] = \
                    IntegralUpperLimit.calc_chi2(like,self.srcName,cl=ul_cl,
                                                skip_global_opt=True,
                                                verbosity = max(verbosity-2,0),
                                                emin=emin, emax=emax,
                                                profile_optimizer=ul_optimizer)
            if ul_type != None:
                spect['fit']['ul'] = dict(flux    = ul_flux,
                                          results = ul_results,
                                          type    = ul_type)

            self.spectra.append(spect)

    def saveProcessedObs(self,filename):
        file=open(filename,'w')
        pickle.dump(self.spectra,file)

    def loadProcessedObs(self,filename):
        file=open(filename,'r')
        spectra=pickle.load(file)
        for spect in spectra:
            self.spectra.append(spect)

    def generateSpec(self):
        vals = []
        pars = []
        for spect in self.spectra:
            np=spect['original']['normpar_name']
            scalef = spect['fit']['flux']/spect['fit']['pars'][np]['value']
            scaled = spect['fit']['dflux']/spect['fit']['pars'][np]['value']
            val = []
            val.append(spect['e_min'])
            val.append(spect['e_max'])
            val.append(spect['fit']['e_mid'])
            if spect['fit'].has_key('ul'):
                val.append(spect['fit']['ul']['flux'])
                val.append(0)
                val.append(spect['fit']['ul']['flux']/scalef*scaled)
                val.append(0)
            else:
                val.append(spect['fit']['flux'])
                val.append(spect['fit']['pars'][np]['error']*scalef)
                val.append(spect['fit']['dflux'])
                val.append(spect['fit']['pars'][np]['error']*scaled)
            val.append(spect['fit']['ts'])
            vals.append(val)
            
        return vals

    def writeSpec(self, filename=None, spect=None,
                  header=True, headstart='% '):
        if spect == None:
            spect = self.generateSpec()
        file = sys.stdout
        if filename != None:
            file=open(filename,'w')
        if header:
            print >>file, '%sColumn 1: Start of energy band [MeV]'%(headstart)
            print >>file, '%sColumn 2: End of energy band [MeV]'%(headstart)
            print >>file, '%sColumn 3: Mid point energy [MeV]'%(headstart)
            print >>file, '%sColumn 4: Integral flux in band [ph/cm^2/s]'%(headstart)
            print >>file, '%sColumn 5: Error on integral flux [ph/cm^2/s]'%(headstart)
            print >>file, '%sColumn 6: Flux density at mid point energy [ph/cm^2/s/MeV]'%(headstart)
            print >>file, '%sColumn 7: Error on flux density [ph/cm^2/s/MeV]'%(headstart)
            print >>file, '%sColumn 8: TS'%(headstart)
        for p in spect:
            s = '%.3f %.3f %.3f %.3e %.3e %.3e %.3e %7.2f'%tuple(p)
            print >>file, s

if __name__ == "__main__":
    import getopt
    def smallHelp(exitcode = 0):
        print "See '%s -h' for more help"%os.path.basename(sys.argv[0])
        sys.exit(exitcode)
    
    def usage(defirf, defft2, defsumfn, defspecfn, tsmin,
              ulfluxerror, tsulbayes, tsulchi2, ulcl, exitcode = 0):
        progname = os.path.basename(sys.argv[0])
        print """usage: %s [--summary] [options] [lc_summary_file...]
   or: %s --compute [options] source_name directory [directory...]

Compute spectra from Fermi data. The program opeartes in two modes:
summary and compute, specified with the --summary (the default) or
--compute options. In the compute mode one or many Fermi observations
are analyzed using the pyLikelihood tools to produce a summary file. In
the summary mode, these summary files are read and the spectrum is
produced.

General options:

-h,--help        print this message.

-o,--output X    specify the name of the summary or spectrum file to
                 write [default: %s (summary mode),
                 %s (compute mode)].

--v              be verbose about doing operations.
--vv             be very verbose.
--vvv            be extremely verbose.

Compute mode options:

--binned         use binned analysis mode

--irf X          specify the IRFs to use [default: %s].

--ft2 X          specify the FT2 file
                 [default: %s].

--tsmin X        set TS value below which background sources are deleted
                 from the model [default: %g].

--fluxerrorul X  set the value of the flux/error below which a Profile
                 likelihood upper limit is calculated (unless it is preempted
                 by the Bayes method based on the TS value) [default: %g]

--tsulbayes X    set TS value below which the Bayesian upper limit is
                 computed for the source flux in the time bin
                 [default: %g]

--tsulchi2 X     set TS value below which the Profile Likelihood upper
                 limit is computed for the source flux in the time bin
                 [default: %g].

--ulcl X         set the confidence limit of upper limits [default: %g]

--fitmodel X     specify filename of XML model from global fit
                 [default: source_name_fitmodel.xml].
"""%(progname,progname,defspecfn,defsumfn,defirf,defft2,tsmin,\
     ulfluxerror,tsulbayes,tsulchi2,ulcl)
        sys.exit(exitcode)


    try:
        optspec = ( 'help', 'output=', 'v', 'vv', 'vvv',
                    'summary', 'compute', 'binned', 'ft2=', 'irf=', 'tsmin=',
                    'fluxerrorul=', 'tsulchi2=', 'tsulbayes=', 'ulcl=',
                    'fitmodel=')
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'vho:', optspec)
    except getopt.GetoptError, err:
        print err
        smallHelp(0)

    defirf     = 'P6_V3_DIFFUSE'
    defft2     = '/sps/hep/glast/users/sfegan/newdata/FT2.fits'
    defsumfn   = 'spec_summary.dat'
    defspecfn  = 'spec.dat'
    deftsmin   = 1
    defulflxdf = 2.0 
    defulbayes = 4
    defulchi2  = -1
    defulcl    = 0.95

    verbose    = 0
    mode       = "summary"
    output     = None
    srcmodel   = None

    irf        = defirf
    ft2        = defft2
    tsmin      = deftsmin
    ulflxdf    = defulflxdf
    ulchi2     = defulchi2
    ulbayes    = defulbayes
    ulcl       = defulcl
    analysis   = 'unbinned'

    for o, a in opts:
        if o in ('-h', '--help'):
            usage(defirf,defft2,defsumfn,defspecfn,deftsmin,
                  defulflxdf,defulbayes,defulchi2,defulcl,0)
        elif o in ('-o', '--output'):
            output = a
        elif o in ('-v', '--v'):
            verbose = 1
        elif o in ('--vv'):
            verbose = 2
        elif o in ('--vvv'):
            verbose = 3
        elif o in ('--summary'):
            mode = 'summary'
        elif o in ('--compute'):
            mode = 'compute'
        elif o in ('--binned'):
            analysis = 'binned'
        elif o in ('--irf'):
            irf = a
        elif o in ('--ft2'):
            ft2 = a
        elif o in ('--fitmodel'):
            srcmodel = a
        elif o in ('--tsmin'):
            tsmin = float(a)
        elif o in ('--fluxerrorul'):
            ulflxdf = float(a)
        elif o in ('--tsulchi2'):
            ulchi2 = float(a)
        elif o in ('--tsulbayes'):
            ulbayes = float(a)
        elif o in ('--ulcl'):
            ulcl = float(a)

    if mode=="summary":
        spec=Spectrum()
        if output == None:
            output = defspecfn
        if len(args)==0:
            spec.loadProcessedObs(defsumfn)
        for f in args:
            spec.loadProcessedObs(f)
        spec.writeSpec(output)
    else:
        if len(args)<2:
            print "Must specify source name and at least one directory!"
            smallHelp()
        source_name = args[0]
        args=args[1:]
        if output == None:
            output = defsumfn
        spec=Spectrum(srcName=source_name,ft2=ft2,irfs=irf,model=srcmodel)
        for d in args:
            spec.globStandardObsDir(d, analysis=analysis)
        if(ulchi2<0): ulchi2=None
        if(ulbayes<0): ulbayes=None
        spec.processAllObs(verbosity=verbose,delete_below_ts=tsmin,
                           ul_flux_dflux = ulflxdf, ul_chi2_ts=ulchi2,
                           ul_bayes_ts=ulbayes, ul_cl=ulcl)
        spec.saveProcessedObs(output)

