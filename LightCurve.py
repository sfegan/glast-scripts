#!/usr/bin/python
# -*-mode:python; mode:font-lock;-*-
"""
@file LightCurve.py

@brief Class to calculate light curves.

@author Stephen Fegan <sfegan@llr.in2p3.fr>

@date 2010-06-22

$Id$
"""

import glob
import os.path
import math
import copy
import pickle
import scipy.stats
import sys
import UnbinnedAnalysis
import BinnedAnalysis
import SummedLikelihood
#import BinnedLikelihood
import IntegralUpperLimit

class MyMath:
    _def_itmax  = 100
    _def_reltol = 1e-14
    
    @staticmethod
    def _gamma_ser(x, a, gammalna = None):
        # See Numerical recipes in C - eq 6.2.5
        if x<=0.0:
            if x==0.0: return 0.0
            else: raise ValueError("Argument x is negative: x=%f"%x)
        if a<=0.0:
            raise ValueError("Argument a is zero or negative: a=%f"%a)
        if gammalna == None:
            gammalna = math.lgamma(a)
        actr = a
        dsum = 1.0/a
        sum = dsum
        for i in range(1,MyMath._def_itmax):
            actr += 1.0
            dsum *= x/actr
            # print i,dsum,sum,sum+dsum
            sum  += dsum
            if math.fabs(dsum) < MyMath._def_reltol*math.fabs(sum):
                return sum*math.exp(a*math.log(x) - x - math.lgamma(a))
        raise RuntimeError("Maximum number of iterations exceeded, x=%f, a=%f"%(x,a))
    
    @staticmethod
    def _gamma_cfrac(x, a, gammalna = None):
        # See Numerical recipes in C - eq 6.2.7 and section 5.2
        if x<=0.0:
            if x==0.0: return 0.0
            else: raise ValueError("Argument x is negative: x=%f"%x)
        if a<=0.0:
            raise ValueError("Argument a is zero or negative: a=%f"%a)
        if gammalna == None:
            gammalna = math.lgamma(a)
        tiny = 1e-30
        A = 0.0
        B = x+1.0-a
        F = B
        if F == 0.0: F = tiny
        C = F
        D = 0.0
        for i in range(1,MyMath._def_itmax):
            A += a + 1.0 - 2.0*i
            B += 2.0
            D = B + A*D
            if D == 0.0: D = tiny
            C = B + A/C
            if C == 0.0: C = tiny
            D = 1.0/D
            delta = C*D
            F *= delta
            # print i,F
            if math.fabs(delta-1.0) < MyMath._def_reltol:
                return math.exp(a*math.log(x) - x - gammalna)/F
        raise RuntimeError("Maximum number of iterations exceeded, x=%f, a=%f"%(x,a))
    
    @staticmethod
    def gammainc(x, a):
        if x<=0.0:
            if x==0.0: return 0.0
            else: raise ValueError("Argument x is negative: x=%f"%x)
        if a<=0.0:
            raise ValueError("Argument a is zero or negative: a=%f"%a)
        if x<a+1.0:
            return MyMath._gamma_ser(x, a)
        else:
            return 1.0-MyMath._gamma_cfrac(x, a)
        
    @staticmethod
    def gammaincc(x, a):
        if x<=0.0:
            if x==0.0: return 0.0
            else: raise ValueError("Argument x is negative: x=%f"%x)
        if a<=0.0:
            raise ValueError("Argument a is zero or negative: a=%f"%a)
        if x<a+1.0:
            return 1.0-MyMath._gamma_ser(x, a)
        else:
            return MyMath._gamma_cfrac(x, a)
    
    @staticmethod
    def gammainv(p, a):
        if p<=0.0:
            if p==0.0: return 0.0
            else: raise ValueError("Argument p is negative: p=%f"%p)
        elif p>=1:
            if p==1: return float('infinity')
            else: raise ValueError("Argument p is greater than unity: p=%f"%p)
        if a<=0:
            raise ValueError("Argument a is zero or negative: a=%f"%a)
    
        gammalna = math.lgamma(a)    
        xtest = a+1.0
        ftest = MyMath._gamma_ser(xtest, a, gammalna)
        ffind = p
        if(ffind<ftest):
            f = lambda x: MyMath._gamma_ser(x, a, gammalna)
            dfdx = lambda x,f: math.exp((a-1.0)*math.log(x) - x - gammalna)
            ffind = p
            if ffind<0.75:
                xtest = math.exp((math.log(ffind) + gammalna + math.log(a))/a)
                if ffind<0.1*MyMath._def_reltol:
                    return xtest
        else:
            f = lambda x: math.log(MyMath._gamma_cfrac(x, a, gammalna))
            dfdx = lambda x,f: -math.exp((a-1.0)*math.log(x) - x - gammalna - f)
            ffind = math.log(1-p)
        ftest = f(xtest)
        dfdxtest = dfdx(xtest, ftest)
        for i in range(1,MyMath._def_itmax):
            xnext = xtest - (ftest-ffind)/dfdxtest
            if xnext <= 0.0:
                xnext = 0.5*(xtest+0.0)
                #print i, xtest, ftest, dfdxtest, xnext, ffind, math.fabs(xnext-xtest), 10*MyMath._def_reltol*(xnext+xtest)
            if math.fabs(xnext-xtest) < 10*MyMath._def_reltol*(xnext+xtest):
                return xnext
            xtest = xnext
            ftest = f(xtest)
            dfdxtest = dfdx(xtest, ftest)
        raise RuntimeError("Maximum number of iterations exceeded, p=%f, a=%f"%(p,a))
    
    @staticmethod
    def gammainvc(p, a):
        if p<=0.0:
            if p==0.0: return 0.0
            else: raise ValueError("Argument p is negative: p=%f"%p)
        elif p>=1:
            if p==1: return float('infinity')
            else: raise ValueError("Argument p is greater than unity: p=%f"%p)
        if a<=0:
            raise ValueError("Argument a is zero or negative: a=%f"%a)
    
        gammalna = math.lgamma(a)    
        xtest = a+1.0
        ftest = MyMath._gamma_cfrac(xtest, a, gammalna)
        ffind = p
        if(ffind<ftest):
            f = lambda x: math.log(MyMath._gamma_cfrac(x, a, gammalna))
            dfdx = lambda x,f: -math.exp((a-1.0)*math.log(x) - x - gammalna - f)
            ffind = math.log(p)
        else:
            f = lambda x: MyMath._gamma_ser(x, a, gammalna)
            dfdx = lambda x,f: math.exp((a-1.0)*math.log(x) - x - gammalna)
            ffind = 1-p
            if ffind<0.75:
                xtest = math.exp((math.log(ffind) + gammalna + math.log(a))/a)
                if ffind<0.1*MyMath._def_reltol:
                    return xtest
        ftest = f(xtest)
        dfdxtest = dfdx(xtest, ftest)
        for i in range(1,MyMath._def_itmax):
            xnext = xtest - (ftest-ffind)/dfdxtest
            if xnext <= 0.0:
                xnext = 0.5*(xtest+0.0)
            #print i, xtest, ftest, dfdxtest, xnext, ffind, math.fabs(xnext-xtest), 10*MyMath._def_reltol*(xnext+xtest)
            if math.fabs(xnext-xtest) < 0.5*MyMath._def_reltol*(xnext+xtest):
                return xnext
            xtest = xnext
            ftest = f(xtest)
            dfdxtest = dfdx(xtest, ftest)
        raise RuntimeError("Maximum number of iterations exceeded, p=%f, a=%f"%(p,a))
    
    @staticmethod
    def chi2cdf(x, a):
        return MyMath.gammainc(0.5*x, 0.5*a)
    
    @staticmethod
    def chi2cdfc(x, a):
        return MyMath.gammaincc(0.5*x, 0.5*a)
    
    @staticmethod
    def chi2inv(p, a):
        return 2.0*MyMath.gammainv(p, 0.5*a)
    
    @staticmethod
    def chi2invc(p, a):
        return 2.0*MyMath.gammainvc(p, 0.5*a)    

class LightCurve:
    """Class to calculate light curves and variability indexes."""
    def __init__(self, srcName=None, ft2=None, irfs=None, model=None,
                 optimizer="Minuit"):
        self.ver = "$Id$"
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

    def globStandardObsDir(self, directory_glob, analysis='unbinned',
                           ft2=None, irfs=None, nbin = 1,
                           sliding_window = False):
        directories = glob.glob(directory_glob)
        directories.sort()
        if nbin == 1:
            for d in directories:
                if os.path.isdir(d):
                    self.addStandardObsDir(d, ft2, irfs, self.obsfiles,
                                           analysis=analysis)
        elif sliding_window == False:
            if self.obsfiles:
                obslist = self.obsfiles.pop()
            else:
                obslist = list()
            for d in directories:
                if len(obslist) == nbin:
                    self.obsfiles.append(obslist)
                    obslist = list()
                if os.path.isdir(d):
                    self.addStandardObsDir(d, ft2, irfs, obslist, 
                                           analysis=analysis)
            if len(obslist) != 0:
                self.obsfiles.append(obslist)
        else:
            if self.obsfiles:
                obslist = self.obsfiles.pop()
            else:
                obslist = list()
            for d in directories:
                if len(obslist) == nbin:
                    self.obsfiles.append(copy.copy(obslist))
                    obslist.pop(0)
                if os.path.isdir(d):
                    self.addStandardObsDir(d, ft2, irfs, obslist, 
                                           analysis=analysis)
            if len(obslist) != 0:
                self.obsfiles.append(obslist)

    def addStandardObsDir(self, directory, ft2=None, irfs=None, obslist=None,
                          analysis='unbinned'):
        prefix = directory+"/"+self.srcName
        ecube = prefix + "_expCube.fits"
        if analysis=='unbinned':
            ft1 = prefix + "_ev_roi.fits"
            emap = prefix + "_expMap.fits"
            self.addUnbinnedObs(ft1, emap, ecube, ft2, irfs, obslist)
        elif analysis=='binned':
            smaps = prefix + "_srcMaps.fits"
            bemap = prefix + "_binExpMap.fits"
            self.addBinnedObs(smaps, bemap, ecube, irfs, obslist)
        else:
            raise NameError("Unknown analysis type: \""+f['analysis']+
                            "\" for directory \""+directory+"\"")

    def addUnbinnedObs(self, ft1, emap, ecube, 
                       ft2=None, irfs=None, obslist=None):
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
        obsfiles = dict(analysis  = 'unbinned',
                        ft1       = ft1,
                        ft2       = _ft2,
                        emap      = emap,
                        ecube     = ecube,
                        irfs      = _irfs)
        if obslist == None:
            self.obsfiles.append(obsfiles)
        else:
            obslist.append(obsfiles)

    def addBinnedObs(self, smaps, bemap, ecube, irfs=None, obslist=None):
        if irfs != None: _irfs = irfs
        else: _irfs = self.irfs
        if not os.path.isfile(smaps):
            raise IOError('SourceMaps file not found: '+smaps);
        if not os.path.isfile(bemap):
            raise IOError('Binned ExpMap not found: '+bemap);
        if not os.path.isfile(ecube):
            raise IOError('ExpCube not found: '+ecube);
        obsfiles = dict(analysis  = 'binned',
                        smaps     = smaps,
                        bemap     = bemap,
                        ecube     = ecube,
                        irfs      = _irfs)
        if obslist == None:
            self.obsfiles.append(obsfiles)
        else:
            obslist.append(obsfiles)
        
    def loadUnbinnedObs(self, f, verbosity=0):
        if verbosity:
            print 'Loading unbinned observation:',f['ft1']
        obs = UnbinnedAnalysis.UnbinnedObs(eventFile=f['ft1'], scFile=f['ft2'],
                                           expMap=f['emap'],expCube=f['ecube'],
                                           irfs=f['irfs'])
        like = UnbinnedAnalysis.UnbinnedAnalysis(obs, srcModel=self.model,
                                                 optimizer=self.optimizer)
        return [ obs, like ]

    def loadBinnedObs(self, f, verbosity=0):
        if verbosity:
            print 'Loading binned observation:',f['smaps']
        obs = BinnedAnalysis.BinnedObs(srcMaps=f['smaps'], expCube=f['ecube'], 
                                       binnedExpMap=f['bemap'], irfs=f['irfs'])
        like = BinnedAnalysis.BinnedAnalysis(obs, srcModel=self.model,
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
                      ul_flux_dflux=0, ul_chi2_ts=None, ul_bayes_ts=4.0,
                      ul_cl=0.95, verbosity=0, emin=0, emax=0, 
                      interim_save_filename=None):
        for f in self.obsfiles:
            lc = dict()
            lc['version'] = self.ver
            lc['config'] = dict()
            lc['config']['fix_shape']       = fix_shape
            lc['config']['delete_below_ts'] = delete_below_ts
            lc['config']['ul_flux_dflux']   = ul_flux_dflux
            lc['config']['ul_chi2_ts']      = ul_chi2_ts
            lc['config']['ul_bayes_ts']     = ul_bayes_ts
            lc['config']['ul_cl']           = ul_cl
            lc['config']['emin']            = emin
            lc['config']['emax']            = emax
            lc['config']['files']           = f
            lc['config']['argv']            = sys.argv

            lc['e_min'] = emin;
            lc['e_max'] = emax;

            if type(f) != list:
                [ obs, like ] = self.loadObs(f,verbosity)
                lc['t_min'] = obs.roiCuts().minTime()
                lc['t_max'] = obs.roiCuts().maxTime()
                if (emin == 0 or emax == 0):
                    lc['e_min'] = obs.roiCuts().getEnergyCuts()[0];
                    lc['e_max'] = obs.roiCuts().getEnergyCuts()[1];
            else:
                lc['t_min'] = None
                lc['t_max'] = None
                like = SummedLikelihood.SummedLikelihood(self.optimizer)
                for ff in f:
                    [ obs, like1 ] = self.loadObs(ff,verbosity)
                    tmin = obs.roiCuts().minTime()
                    tmax = obs.roiCuts().maxTime()
                    if lc['t_min'] == None or tmin<lc['t_min']:
                        lc['t_min'] = tmin 
                    if lc['t_max'] == None or tmax>lc['t_max']:
                        lc['t_max'] = tmax
                    if (lc['e_min'] == 0 or lc['e_max'] == 0):
                        ecuts = obs.roiCuts().getEnergyCuts()
                        lc['e_min'] = ecuts[0]
                        lc['e_max'] = ecuts[1]
                    elif (emin == 0 or emax == 0):
                        ecuts = obs.roiCuts().getEnergyCuts()
                        lc['e_min'] = max(lc['e_min'], ecuts[0])
                        lc['e_max'] = min(lc['e_max'], ecuts[1])
                    like.addComponent(like1)

            emin = lc['e_min']
            emax = lc['e_max']
            
            like.tol = like.tol*0.01;

            if verbosity > 1:
                print '- Time:',lc['t_min'],'to',lc['t_max']

            src = like[self.srcName]
            if src == None:
                raise NameError("No source \""+self.srcName+"\" in model "+
                                self.model)
            srcfreepar=like.freePars(self.srcName)
            srcnormpar=like.normPar(self.srcName)
            if len(srcfreepar)>0:
                like.setFreeFlag(self.srcName, srcfreepar, 0)
                like.syncSrcParams(self.srcName)

            meanvalue = srcnormpar.getValue()
            meanerror = srcnormpar.error()
            lc['original']=dict()
            lc['original']['normpar_init_value'] = meanvalue
            lc['original']['normpar_name'] = srcnormpar.getName()
            lc['original']['nfree'] = len(like.freePars(self.srcName))
            lc['original']['flux'] = like[self.srcName].flux(emin, emax)
            lc['original']['logL'] = like.logLike.value()
            if verbosity > 1:
                print '- Original log Like:',lc['original']['logL']

            if fix_shape:
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

            # ----------------------------- FIT 1 -----------------------------

            if verbosity > 1:
                print '- Fit 1 - All parameters of',self.srcName,'fixed'
            like.fit(max(verbosity-3, 0))

            lc['allfixed'] = dict()
            lc['allfixed']['logL'] = like.logLike.value()
            fitstat = like.optObject.getRetCode()
            if verbosity > 1 and fitstat != 0:
                print "- Fit 1 - Minimizer returned with code: ", fitstat
            lc['allfixed']['fitstat'] = fitstat
            if verbosity > 1:
                print '- Fit 1 - log Like:',lc['allfixed']['logL']

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
                        print '- Fit 1 - refitting model'
                    like.fit(max(verbosity-3, 0))
                    lc['allfixed']['fitstat_initial'] = \
                        lc['allfixed']['fitstat']
                    fitstat = like.optObject.getRetCode()
                    if verbosity > 1 and fitstat != 0:
                        print "- Fit 1 - Minimizer returned with code: ",\
                            fitstat
                    lc['allfixed']['fitstat'] = fitstat
                    lc['allfixed']['logL'] = like.logLike.value()
                    if verbosity > 1:
                        print '- Fit 1 - log Like:',lc['allfixed']['logL']
                        

            lc['allfixed']['flux']=like[self.srcName].flux(emin, emax)
            pars = dict()
            for pn in like[self.srcName].funcs['Spectrum'].paramNames:
                p = like[self.srcName].funcs['Spectrum'].getParam(pn)
                pars[p.getName()] = dict(name      = p.getName(),
                                         value     = p.getTrueValue(),
                                         error     = p.error()*p.getScale(),
                                         free      = p.isFree())
            lc['allfixed']['pars'] = pars

            # ------------------ N SIGMA PROFILE LIKELIHOOD -------------------

            prof_sigma = (-1,-0.5,0,0.5,1.0)
            lc['profile'] = dict();
            lc['profile']['sigma'] = []
            lc['profile']['value'] = []
            lc['profile']['logL'] = []
            lc['profile']['flux'] = []
            lc['profile']['fitstat'] = []

            if verbosity > 1:
                print '- Fit 1 - generating %d point likelihood profile'%\
                      len(prof_sigma)
            for sigma in prof_sigma:
                val = sigma*meanerror+meanvalue
                if val < srcnormpar.getBounds()[0]:
                    val = srcnormpar.getBounds()[0]
                if (lc['profile']['value']
                    and lc['profile']['value'][-1]==val):
                    continue
                lc['profile']['value'].append(val)
                lc['profile']['sigma'].append((val-meanvalue)/meanerror)
                if(val == meanvalue):
                    lc['profile']['logL'].append(lc['allfixed']['logL'])
                    lc['profile']['flux'].append(lc['allfixed']['flux'])
                else:
                    srcnormpar.setValue(val)
                    like.syncSrcParams(self.srcName)                    
                    like.fit(max(verbosity-3, 0))
                    fitstat = like.optObject.getRetCode()
                    if verbosity > 2 and fitstat != 0:
                        print "- Fit 1 - profile: Minimizer returned code: ",\
                            fitstat
                    lc['profile']['fitstat'].append(fitstat)
                    lc['profile']['logL'].append(like.logLike.value())
                    lc['profile']['flux'].append(like[self.srcName].\
                                              flux(emin, emax))
                if verbosity > 2:
                    print '- Fit 1 - profile: %+g, %f -> %f'%\
                          (sigma,lc['profile']['value'][-1],
                           lc['profile']['logL'][-1]-lc['allfixed']['logL'])

            srcnormpar.setValue(meanvalue)
            like.syncSrcParams(self.srcName)                    

            # ----------------------------- FIT 2 -----------------------------

            if verbosity > 1:
                print '- Fit 2 - Normalization parameter of',\
                      self.srcName,'free'
            srcnormpar.setFree(1)
            like.syncSrcParams(self.srcName)
            like.fit(max(verbosity-3, 0))
            lc['normfree'] = dict()
            fitstat = like.optObject.getRetCode()
            if verbosity > 1 and fitstat != 0:
                print "- Fit 2 - Minimizer returned with code: ", fitstat
            lc['normfree']['fitstat'] = fitstat
            lc['normfree']['logL'] = like.logLike.value()
            lc['normfree']['ts'] = like.Ts(self.srcName)
            lc['normfree']['flux_dflux'] = \
                srcnormpar.getValue()/srcnormpar.error()
            if verbosity > 1:
                print '- Fit 2 - log Like:',lc['normfree']['logL'],\
                      '(TS='+str(lc['normfree']['ts'])+')'

            lc['normfree']['nfree']=len(like.freePars(self.srcName))
            lc['normfree']['flux']=like[self.srcName].flux(emin, emax)
            pars = dict()
            for pn in like[self.srcName].funcs['Spectrum'].paramNames:
                p = like[self.srcName].funcs['Spectrum'].getParam(pn)
                pars[p.getName()] = dict(name      = p.getName(),
                                         value     = p.getTrueValue(),
                                         error     = p.error()*p.getScale(),
                                         free      = p.isFree())
            lc['normfree']['pars'] = pars

            ul_type = None
            if ul_bayes_ts != None and lc['normfree']['ts'] < ul_bayes_ts:
                ul_type = 'bayesian'
                [ul_flux, ul_results] = \
                    IntegralUpperLimit.calc_int(like,self.srcName,cl=ul_cl,
                                                skip_global_opt=True,
                                                verbosity = max(verbosity-2,0),
                                                emin=emin, emax=emax,
                                            poi_values = lc['profile']['value'])
            elif ( ul_flux_dflux != None and \
                   lc['normfree']['flux_dflux'] < ul_flux_dflux ) or \
                   ( ul_chi2_ts != None and lc['normfree']['ts'] < ul_chi2_ts):
                ul_type = 'chi2'
                [ul_flux, ul_results] = \
                    IntegralUpperLimit.calc_chi2(like,self.srcName,cl=ul_cl,
                                                 skip_global_opt=True,
                                                 verbosity = max(verbosity-2,0),
                                                 emin=emin, emax=emax)
            if ul_type != None:
                lc['normfree']['ul'] = dict(flux    = ul_flux,
                                            results = ul_results,
                                            type    = ul_type)

            # ----------------------------- FIT 3 -----------------------------

            if verbosity > 1:
                print '- Fit 3 - All parameters of',self.srcName,'free'
            like.setFreeFlag(self.srcName, srcfreepar, 1)
            like.syncSrcParams(self.srcName)
            like.fit(max(verbosity-3, 0))
            lc['allfree'] = dict()
            fitstat = like.optObject.getRetCode()
            if verbosity > 1 and fitstat != 0:
                print "- Fit 3 - Minimizer returned with code: ", fitstat
            lc['allfree']['fitstat'] = fitstat
            lc['allfree']['logL'] = like.logLike.value()
            lc['allfree']['ts'] = like.Ts(self.srcName)
            if verbosity > 1:
                print '- Fit 3 - log Like:',lc['allfree']['logL'],\
                      '(TS='+str(lc['allfree']['ts'])+')'
            lc['allfree']['nfree']=len(like.freePars(self.srcName))
            lc['allfree']['flux']=like[self.srcName].flux(emin, emax)
            pars = dict()
            for pn in like[self.srcName].funcs['Spectrum'].paramNames:
                p = like[self.srcName].funcs['Spectrum'].getParam(pn)
                pars[p.getName()] = dict(name      = p.getName(),
                                         value     = p.getTrueValue(),
                                         error     = p.error()*p.getScale(),
                                         free      = p.isFree())
            lc['allfree']['pars'] = pars

            self.lc.append(lc)
            if interim_save_filename != None:
                self.saveProcessedObs(interim_save_filename)

    def saveProcessedObs(self,filename):
        file=open(filename,'w')
        pickle.dump(self.lc,file)

    def loadProcessedObs(self,filename):
        file=open(filename,'r')
        lcs=pickle.load(file)
        for lc in lcs:
            self.lc.append(lc)

    def generateLC(self, verbosity=0):
        # First: calculate logL of fixed flux model at true minimum - hoping
        # it lies somewhere in the profile we computed
        first = True
        profile_x = []
        profile_y = []
        for lc in self.lc:
            if first:
                profile_x = lc['profile']['value']
                profile_y = lc['profile']['logL']
                first = False
            else:
                profile_y = map(lambda x,y:x+y,lc['profile']['logL'],profile_y)

        p = scipy.polyfit(profile_x, profile_y, 2);
        prof_max_val = -p[1]/(2*p[0])
        prof_max_logL = p[2]-p[1]*p[1]/(4*p[0])
        if (prof_max_val<min(profile_x)) or (prof_max_val>max(profile_x)):
            print "Warning: corrected minimum %f is outside profile range [%f to %f]" \
                  %(prof_max_val,min(profile_x),max(profile_x))
            print profile_x, profile_y

        profile_fity = scipy.polyval(p,profile_x)
        profile_max_diff = max(map(lambda x,y:abs(x-y),profile_y,profile_fity))
        if profile_max_diff>0.5:
            print "Warning: large difference between profile and fit: %f"%profile_max_diff
            print profile_x, profile_y, profile_fity

        if verbosity>0:
            print profile_x, profile_y, profile_fity

        # Second: process data for LC, accumulating required values to
        # allow calculation of variability stats

        vals = []
        pars = []
        dchi2_specfree     = 0
        dchi2_normfree     = 0
        dchi2_normfree_alt = 0
        dchi2_normfree_ul  = 0
        allfixed_logL      = 0
        allfixed_val       = 0
        npar_specfree      = 0
        npar_normfree      = 0
        first = True

        for lc in self.lc:
            np=lc['original']['normpar_name']
            if first:
                pars.append(np)
                allfixed_val = lc['original']['normpar_init_value']
            scale=lc['normfree']['flux']/lc['normfree']['pars'][np]['value']
            val = []
            val.append(lc['t_min']/86400 + 51910)
            val.append(lc['t_max']/86400 + 51910)
            if lc['normfree'].has_key('ul'):
                val.append(lc['normfree']['ul']['flux'])
                val.append(0)
            else:
                val.append(lc['normfree']['flux'])
                val.append(lc['normfree']['pars'][np]['error']*scale)
            val.append(lc['normfree']['ts'])
            val.append(lc['allfree']['flux'])
            val.append(lc['allfree']['pars'][np]['error']*scale)
            for p in lc['allfree']['pars']:
                if p != np and lc['allfree']['pars'][p]['free'] == True:
                    if first: pars.append(p)
                    val.append(lc['allfree']['pars'][p]['value'])
                    val.append(lc['allfree']['pars'][p]['error'])
            val.append(lc['allfree']['ts'])

            allfixed_logL += lc['allfixed']['logL']
            dchi2_specfree += 2*(lc['allfree']['logL']-lc['normfree']['logL'])
            dchi2_normfree_alt += lc['normfree']['logL']
            
            # Arbitrarily assume a quadratic is an OK fit
            y = lc['profile']['logL']
            p = scipy.polyfit(profile_x, y, 2);
            dchi2_normfree += 2*(lc['normfree']['logL']
                                 - scipy.polyval(p, prof_max_val))

            if (lc['normfree'].has_key('ul') and
                lc['normfree']['ul']['type'] == 'bayesian'):
                # Arbitrarily assume a quadratic is an OK fit
                y = lc['normfree']['ul']['results']['poi_chi2_equiv']
                p = scipy.polyfit(profile_x, y, 2);
                dchi2_normfree_ul += scipy.polyval(p, prof_max_val)
            else:
                dchi2_normfree_ul += 2*(lc['normfree']['logL']
                                        - scipy.polyval(p, prof_max_val))
            if not first:
                npar_specfree += lc['allfree']['nfree']-lc['normfree']['nfree']
                npar_normfree += lc['normfree']['nfree']
            first = False

            vals.append(val)

        dchi2_normfree_alt = 2*(dchi2_normfree_alt-prof_max_logL)
        corr_logL = prof_max_logL - allfixed_logL
        
        if(abs(dchi2_normfree-dchi2_normfree_alt) > 0.01):        
            print "Warning: normfree log likelhood calculations differ by more than 0.01"
            print dchi2_normfree, dchi2_normfree_alt, dchi2_normfree_ul

        stats = dict(dchi2_specfree            = dchi2_specfree,
                     dchi2_normfree            = dchi2_normfree,
                     dchi2_normfree_ul         = dchi2_normfree_ul,
                     npar_specfree             = npar_specfree,
                     npar_normfree             = npar_normfree,
                     pars                      = pars,
                     prof_x                    = profile_x,
                     prof_y                    = profile_y,
                     prof_max_val              = prof_max_val,
                     prof_max_logL             = prof_max_logL,
                     prof_corr_logL            = corr_logL,
                     allfixed_val              = allfixed_val,
                     allfixed_logL             = allfixed_logL)
        return vals, stats

    def writeLC(self, filename=None, lc=None, stats=None,
                header=True, headstart='% ', verbosity=0):
        if lc == None or stats == None:
            [lc, stats] = self.generateLC(verbosity=verbosity)
        file = sys.stdout
        if filename != None:
            file=open(filename,'w')
        if header:
            # print >>file, '%sOptions: %s'%(headstart,' '.join(lc[0]['config']['argv'][1:]))
            chi2 = stats['dchi2_normfree']
            ndof = stats['npar_normfree']
            prob = MyMath.chi2cdfc(chi2,ndof)
            sigma = math.sqrt(MyMath.chi2invc(prob,1))
            print >>file, '%sVariable flux (no UL): chi^2=%.3f (%d DOF) - Pr(>X)=%g (~%g sigma)'%(headstart,chi2,ndof,prob,sigma)
            chi2 = stats['dchi2_normfree_ul']
            ndof = stats['npar_normfree']
            prob = MyMath.chi2cdfc(chi2,ndof)
            sigma = math.sqrt(MyMath.chi2invc(prob,1))
            print >>file, '%sVariable flux (w/UL):  chi^2=%.3f (%d DOF) - Pr(>X)=%g (~%g sigma)'%(headstart,chi2,ndof,prob,sigma)
            chi2 = stats['dchi2_specfree']
            ndof = stats['npar_specfree']
            prob = MyMath.chi2cdfc(chi2,ndof)
            sigma = math.sqrt(MyMath.chi2invc(prob,1))
            print >>file, '%sVariable spectrum:     chi^2=%.3f (%d DOF) - Pr(>X)=%g (~%g sigma)'%(headstart,chi2,ndof,prob,sigma)
            print >>file, '%sProfile minimum: %f (search range: %f to %f)'%(headstart,stats['prof_max_val'],min(stats['prof_x']),max(stats['prof_x']))
            print >>file, '%sLogL correction: %f (WRT logL @ prescribed val of %g)'%(headstart,stats['prof_corr_logL'],stats['allfixed_val'])

            print >>file, '%sColumn 1: Start of time bin [MJD]'%(headstart)
            print >>file, '%sColumn 2: End of time bin [MJD]'%(headstart)
            print >>file, '%sColumn 3: Fixed spectral shape: Flux [ph/cm^2/s]'%(headstart)
            print >>file, '%sColumn 4: Fixed spectral shape: Error on Flux [ph/cm^2/s]'%(headstart)
            print >>file, '%sColumn 5: Fixed spectral shape: TS'%(headstart)
            print >>file, '%sColumn 6: Optimized spectral shape: Flux [ph/cm^2/s]'%(headstart)
            print >>file, '%sColumn 7: Optimized spectral shape: Error on Flux [ph/cm^2/s]'%(headstart)
            nc=8
            for i in range(1,len(stats['pars'])):
                pn = stats['pars'][i]
                print >>file, '%sColumn %d: Optimized spectral shape: %s'%(headstart,nc+i-1,pn)
                print >>file, '%sColumn %d: Optimized spectral shape: Error on %s'%(headstart,nc+i,pn)
                nc+=2
            print >>file, '%sColumn %d: Optimized spectral shape: TS'%(headstart,nc+i-1)
        for p in lc:
            s = '%.3f %.3f %.3e %.3e %7.2f'%(p[0],p[1],p[2],p[3],p[4])
            for i in range(5,len(p)-1):
                s += ' %.3e'%(p[i])
            s += ' %7.2f'%(p[-1])
            print >>file, s


if __name__ == "__main__":
    import getopt
    def smallHelp(exitcode = 0):
        print "See '%s -h' for more help"%os.path.basename(sys.argv[0])
        sys.exit(exitcode)
    
    def usage(defirf, defft2, defsumfn, deflcfn, tsmin,
              ulfluxerror, tsulbayes, tsulchi2,
              ulcl, opt, exitcode = 0):
        progname = os.path.basename(sys.argv[0])
        print """usage: %s [--summary] [options] [lc_summary_file...]
   or: %s --compute [options] source_name directory [directory...]

Compute lightcurves from Fermi data. The program opeartes in two modes:
summary and compute, specified with the --summary (the default) or
--compute options. In the compute mode one or many Fermi observations
are analyzed using the pyLikelihood tools to produce a summary file. In
the summary mode, these summary files are read and the lightcurve is
produced.

General options:

-h,--help        print this message.

-o,--output X    specify the name of the summary or lightcurve file to
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

--tsulbayes X    set TS value below which the Bayesian upper limit is
                 computed for the source flux in the time bin
                 [default: %g]

--tsulchi2 X     set TS value below which the Profile Likelihood upper
                 limit is computed for the source flux in the time bin
                 [default: %g].

--fluxerrorul X  set the value of the flux/error below which a Profile
                 likelihood upper limit is calculated (unless it is preempted
                 by the Bayes method based on the TS value) [default: %g]

--ulcl X         set the confidence limit of upper limits [default: %g]

--fitmodel X     specify filename of XML model from global fit
                 [default: source_name_fitmodel.xml].

--rebin X        combine X time bins into one for the analysis (i.e. rebin
                 the LC).

--sliding_window rebin the time bins using a sliding window so that they
                 overlap

--opt X          use optimizer X [defaul: %s]
"""%(progname,progname,deflcfn,defsumfn,defirf,defft2,tsmin,\
     ulfluxerror,tsulbayes,tsulchi2,ulcl,opt)
        sys.exit(exitcode)


    try:
        optspec = ( 'help', 'output=', 'v', 'vv', 'vvv',
                    'summary', 'compute', 'binned', 'ft2=', 'irf=', 'tsmin=',
                    'fluxerrorul=', 'tsulchi2=', 'tsulbayes=', 'ulcl=',
                    'fitmodel=', 'rebin=', 'sliding_window', 'opt=')
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'vho:', optspec)
    except getopt.GetoptError, err:
        print err
        smallHelp(0)

    defirf     = 'P7SOURCE_V6'
    defft2     = '/sps/hep/glast/data/FSSCWeeklyData/FT2.fits'
    defsumfn   = 'lc_summary.dat'
    deflcfn    = 'lc.dat'
    deftsmin   = 1
    defulflxdf = 2.0 
    defulbayes = 0
    defulchi2  = 4
    defulcl    = 0.95
    defopt     = "MINUIT"

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
    nbin       = 1
    sliding    = False
    analysis   = 'unbinned'
    opt        = defopt

    for o, a in opts:
        if o in ('-h', '--help'):
            usage(defirf,defft2,defsumfn,deflcfn,deftsmin,
                  defulflxdf,defulbayes,defulchi2,defulcl,defopt,0)
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
        elif o in ('--rebin'):
            nbin = int(a)
        elif o in ('--sliding_window'):
            sliding = True
        elif o in ('--opt'):
            opt = a

    if mode=="summary":
        lc=LightCurve()
        if output == None:
            output = deflcfn
        if len(args)==0:
            lc.loadProcessedObs(defsumfn)
        for f in args:
            lc.loadProcessedObs(f)
        lc.writeLC(output,verbosity=verbose)
    else:
        if len(args)<2:
            print "Must specify source name and at least one directory!"
            smallHelp()
        source_name = args[0]
        args=args[1:]
        if output == None:
            output = defsumfn
        lc=LightCurve(srcName=source_name,ft2=ft2,irfs=irf,model=srcmodel,\
                      optimizer=opt)
        for d in args:
            lc.globStandardObsDir(d, nbin=nbin, analysis=analysis,
                                  sliding_window = sliding)
        if(ulchi2<0): ulchi2=None
        if(ulbayes<0): ulbayes=None
        lc.processAllObs(verbosity=verbose, delete_below_ts=tsmin,
                         ul_chi2_ts=ulchi2, ul_flux_dflux = ulflxdf,
                         ul_bayes_ts=ulbayes, ul_cl=ulcl,
                         interim_save_filename=output)
        
