#!/usr/bin/python
# -*-mode:python; mode:font-lock;-*-
"""
@file ROILikelihoodOptimizer.py

@brief Class to optimize Likelihood of ROI model

@author Stephen Fegan <sfegan@llr.in2p3.fr>

@date 2011-04-13

$Id: ROILikelihoodOptimizer.py 2795 2011-05-06 14:48:45Z sfegan $
"""

import os.path
import numpy
import math
import pickle

import pyLikelihood as pyLike
from LikelihoodState import LikelihoodState

class ROILikelihoodOptimizer:
    """Class to optimize Likelihood of ROI model (a replacement for gtlike)."""
    def __init__(self, like, sourcesOfInterest=None, optimizer="Minuit",
                 tol=1e-8, chatter=3, 
                 freeze_nuisance_sources_immediately = False,
                 freeze_nuisance_sources_after_optimize = False,
                 nuisance_npred_frac_max = 0.05,
                 nuisance_soi_sep_min_deg = 5.0,
                 calculate_full_ts_for_all = False):
        self.ver = "$Id: ROILikelihoodOptimizer.py 2795 2011-05-06 14:48:45Z sfegan $"
        self.res = {}
        self._like = like
        self._original_state = LikelihoodState(self._like)
        self._chatter = 0
        self._SOI = []
        self._freeze_nuisance_immediately = freeze_nuisance_sources_immediately
        self._freeze_nuisance_after_optimize = \
            freeze_nuisance_sources_after_optimize
        self._nuisance_npred_frac_max = nuisance_npred_frac_max
        self._nuisance_soi_sep_min_deg = nuisance_soi_sep_min_deg
        self._calculate_full_ts_for_all = calculate_full_ts_for_all

        if sourcesOfInterest is not None:
            if type(sourcesOfInterest) != list:
                sourcesOfInterest = [ sourcesOfInterest ]
            for s in sourcesOfInterest:
                if s in like.sourceNames():
                    self._SOI.append(s)
                else:
                    raise RuntimeError("Invalid source of interest: " + s)
        if optimizer:
            self._like.optimizer = optimizer
        if tol:
            self._like.tol = tol
        if chatter:
            self._chatter = chatter
        
    def _nuisanceSourceNames(self, SOI = None, sep_min_deg = None, 
                             npred_frac_max = None):
        if SOI is None:
            SOI = self._SOI
        if type(SOI) != list:
            SOI = [ SOI ]
        if npred_frac_max is None:
            npred_frac_max = self._nuisance_npred_frac_max
        if sep_min_deg is None:
            sep_min_deg = self._nuisance_soi_sep_min_deg
        sep_min_rad = sep_min_deg/180.0*math.pi
        nuisance = []
        npred_total = 0
        for sn in self._like.sourceNames():
            npred_total += self._like.NpredValue(sn)
        npred_thresh = npred_total * npred_frac_max
        for sn in self._like.sourceNames():
            if sn in SOI:
                continue
            s = self._like[sn]
            if s.type != 'PointSource':
                continue
            ps = pyLike.PointSource_cast(s.src)
            if ps.fixedSpectrum():
                continue
            if self._like.NpredValue(sn) > npred_thresh:
                continue
            d = ps.getDir()
            min_sep = math.pi
            for soi_sn in SOI:
                soi_s = self._like[soi_sn]
                soi_ps = pyLike.PointSource_cast(soi_s.src)
                soi_d = soi_ps.getDir()
                sep = d.difference(soi_d)
                if(sep < min_sep):
                    min_sep = sep
            if min_sep < sep_min_rad:
                continue
            nuisance.append(sn)
        return nuisance

    def _freeze_sources(self):
        nuisance_sources = self._nuisanceSourceNames()
        for sn in nuisance_sources:
            srcfreepar = self._like.freePars(sn)
            self._like.setFreeFlag(sn, srcfreepar, False)
            self._like.syncSrcParams(sn)
        return nuisance_sources

    def restoreOriginalState():
        self._original_state.restore()

    def run(self, noFit=False):
        L = self._like
        start_state = LikelihoodState(L)

        if(self._freeze_nuisance_immediately):
            nuisance_sources = self._freeze_sources()
            if self._chatter > 0:
                for sn in nuisance_sources:
                    print "Freezing source:",sn 
        
        if(self._freeze_nuisance_after_optimize):
            L.optimize()
            nuisance_sources = self._freeze_sources()
            if self._chatter > 0:
                for sn in nuisance_sources:
                    print "Freezing source:",sn 

        if not noFit:
            L.fit()
     
        res = {}
        res['version']                  = self.ver
        res['like_val']                 = L.logLike.value()
        res['fit_state']                = L.optObject.getRetCode()
        res['cov_matrix']               = L.optObject.covarianceMatrix()

        res['src'] = {}
        npred_total = 0
        nfree_param = 0
        for sn in L.sourceNames():
            s = L[sn]
            ss = s.src

            src_info = {}
            src_info["type"]            = ss.getType()
            src_info["fixed"]           = ss.fixedSpectrum()

            if not src_info["fixed"] and src_info["type"] == 'Point':
                if self._chatter > 0:
                    print "Calculating approximate TS for:",sn
                src_info['TS_approx']   = L.Ts(sn,reoptimize=False)
                if sn in self._SOI or self._calculate_full_ts_for_all:
                    if self._chatter > 0:
                        print "Calculating full TS for:",sn
                    src_info['TS']      = L.Ts(sn,reoptimize=True)

            # Spectrum parameters
            spec = ss.spectrum()
            spec_param_names = s.funcs['Spectrum'].paramNames
            src_info["spec_type"]       = spec.genericName()
            src_info["spec_free_par"]   = {}
            spec_info = {}
            for pn in spec_param_names:
                param = spec.getParam(pn)
                param_info = {}
                param_info['free']            = param.isFree()
                if param.isFree():
                    src_info["spec_free_par"][pn] = nfree_param
                    param_info['free_iparam'] = nfree_param
                    param_info['error']       = param.error()
                    param_info['true_error']  = param.error()*param.getScale()
                    nfree_param+=1
                param_info['true_value']      = param.getTrueValue()
                param_info['value']           = param.getValue()
                param_info['scale']           = param.getScale()
                param_info['bounds']          = param.getBounds()
                spec_info[pn] = param_info
            cov_m = []
            for ipn in src_info["spec_free_par"]:
                cov = {}
                cov_v = []
                for jpn in src_info["spec_free_par"]:
                    iparam = spec_info[ipn]['free_iparam']
                    jparam = spec_info[jpn]['free_iparam']
                    cov[jpn] = res['cov_matrix'][iparam][jparam]
                    cov_v.append(cov[jpn])
                spec_info[ipn]['cov'] = cov
                cov_m.append(cov_v)
            src_info["spec_par"]     = spec_info
            src_info["spec_cov"]     = cov_m
            cov_m = numpy.matrix(cov_m)

            # Flux value, derivatives and error
            info = {}
            info['value']              = ss.flux()
            if not ss.fixedSpectrum():
                info["deriv"]          = {}
                v=[]
                for pn in src_info["spec_free_par"]:
                    x = ss.fluxDeriv(pn)
                    info["deriv"][pn]  = x
                    v.append(x)
                v = numpy.matrix(v)
                src_info["error"]      = math.sqrt(v*cov_m*v.transpose())
            src_info["flux"]         = info

            # Energy flux value, derivatives and error
            info = {}
            info['value']              = ss.energyFlux()
            if not ss.fixedSpectrum():
                info["deriv"]          = {}
                v=[]
                for pn in src_info["spec_free_par"]:
                    x = ss.energyFluxDeriv(pn)
                    info["deriv"][pn]  = x
                    v.append(x)
                v = numpy.matrix(v)
                info["error"]          = math.sqrt(v*cov_m*v.transpose())
            src_info["energy_flux"]  = info 

            # Npred value, derivatives and error
            npred = L.NpredValue(sn)
            npred_total += npred
            info = {}
            info['value']              = npred
#            if not ss.fixedSpectrum():
#                info["deriv"]          = {}
#                v = []
#                for pn in src_info["spec_free_par"]:
#                    x = 0 #ss.NpredDeriv(pn) CRASH
#                    info["deriv"][pn]  = x
#                    v.append(x)
#                v = numpy.matrix(v)
#                info["error"]          = math.sqrt(v*cov_m*v.transpose())
            src_info["npred"]        = info
 
            # Spectral plots

            # Set source results
            res['src'][sn] = src_info
            
        res['total_nobs']               = L.total_nobs();
        res['total_npred']              = npred_total
        
        self.res = res
