"""
@file IntegralUpperLimits.py

@brief Function to calculate upper limits by integrating Likelihood function
       to given "probability" level.

@author Stephen Fegan <sfegan@llr.in2p3.fr>

$Id: IntegralUpperLimit.py 640 2009-04-17 06:02:38Z sfegan $

See help for IntegralUpperLimits.calc for full details.
"""

import UnbinnedAnalysis
import scipy.integrate
import scipy.interpolate
import scipy.optimize
import math

# These functions added 2009-04-01 to make better initial guesses for
# nuisence parameters by extrapolating them from previous iterations.
# This makes Minuit quicker (at least when using strategy 0)

def _guess_nuisance(x, like, cache):
    """Internal function used by the SciPy integrator to evaluate the
    likelihood function. Not intended for use outside of this package."""
    X = cache.keys()
    X.sort()
    if len(X)<2 or x>max(X) or x<min(X):
        return
    icache = 0
    for iparam in range(len(like.model.params)):
        if(like.model[iparam].isFree()):
            Y = []
            for ix in X: Y.append(cache[ix][icache])
            # Simple interpolation is best --- Do not try splines!
            p = scipy.interpolate.interp1d(X,Y)(x)[0]
            limlo, limhi = like.model[iparam].getBounds()
            p = max(limlo, min(p, limhi))
            like.model[iparam].setValue(p)
            like.logLike.syncSrcParams(like[iparam].srcName)
            icache += 1

def _cache_nuisance(x, like, cache):
    """Internal function used by the SciPy integrator to evaluate the
    likelihood function. Not intended for use outside of this package."""
    params = []
    for iparam in range(len(like.model.params)):
        if(like.model[iparam].isFree()):
            params.append(like.model[iparam].value())
    cache[x] = params

def _loglike(x, like, par, srcName, offset, verbose, no_optimizer,
             nuisance_cache):
    """Internal function used by the SciPy integrator to evaluate the
    likelihood function. Not intended for use outside of this package."""

    # Optimizer uses verbosity level one smaller than given here
    optverbose = max(verbose-1, 0)

    par.setFree(0)
    par.setValue(x)
    like.logLike.syncSrcParams(srcName)

    # This flag skips calling the optimizer - and is used in the case when
    # all parameters are frozen, since some optimizers might have problems
    # being called with nothing to do
    if not no_optimizer:
        try:
            if nuisance_cache != None:
                _guess_nuisance(x, like, nuisance_cache)
            like.fit(optverbose)
            if nuisance_cache != None:
                _cache_nuisance(x, like, nuisance_cache)
        except RuntimeError:
            like.fit(optverbose)
            if nuisance_cache != None:
                _cache_nuisance(x, like, nuisance_cache)
            pass
        pass
    
    return like.logLike.value() - offset

def _integrand(x, f_of_x, like, par, srcName, maxval, verbose=0,
               no_optimizer = False, nuisance_cache = None):
    """Internal function used by the SciPy integrator to evaluate the
    likelihood function. Not intended for use outside of this package."""

    f = math.exp(_loglike(x,like,par,srcName,maxval,verbose,no_optimizer,
                          nuisance_cache))
    f_of_x[x] = f
    if verbose:
        print "Function evaluation:", x, f
    return f

def _root(x, root_cache, like, par, srcName, subval, verbose=0,
          no_optimizer = False, nuisance_cache = None):
    """Internal function used by the SciPy root finder to evaluate the
    likelihood function. Not intended for use outside of this package."""

    if root_cache.has_key(x):
        f = root_cache[x]
    else:
        f = _loglike(x,like,par,srcName,subval,verbose,no_optimizer,
                     nuisance_cache)
        root_cache[x]=f
    if verbose:
        print "Root evaluation:", x, f
    return f

def calc(like, srcName, ul=0.95,\
         verbose=0, be_very_careful=False, freeze_all=True,
         delta_log_like_limits = 10.0):
    """Calculate an integral upper limit by direct integration.

  Description:

    Calculate an integral upper limit by integrating the likelihood
    function up to a point which contains a given fraction of the
    total probability. This is a fairly standard Bayesian approach to
    calculating upper limits, which assumes a uniform prior
    probability.  The likelihood function is not assumed to
    bedistributed as chi-squared.

    This function first uses the optimizer to find the global minimum,
    then uses the scipy.integrate.quad function to integrate the
    likelihood function with respect to one of the parameters. During
    the integration, the other parameters can be frozen at their
    values found in the global minimum or optimized freely at each
    point.

  Inputs:

    like -- a binned or unbinned likelihood object which has the
            desired model. Be careful to freeze the index of the
            source for which the upper limit is being if you want to
            quote a limit with a fixed index.
    srcName -- the name of the source for which to compute the limit.
    ul -- probability level for the upper limit.
    verbose -- verbosity level. A value of zero means no output will
               be written. With a value of one the function writes
               some values describing its progress, but the optimizers
               don't write anything. Values larger than one direct the
               optimizer to produce verbose output.
    be_very_careful -- direct the integrator to be even more careful
                       in integrating the function, by telling it to
                       use a higher tolerance and to specifically pay
                       attention to the peak in the likelihood function.
                       More evaluations of the integrand will be made,
                       which WILL be slower and MAY result in a more
                       accurate limit.
    freeze_all -- freeze all other parameters at the values of the
                  global minimum.
    delta_log_like_limits -- the limits on integration is defined by
                             the region around the global maximum in
                             which the log likelihood is close enough
                             to the peak value. Too small a value will
                             mean the integral does not include a
                             significant amount of the likelihood function.
                             Too large a value may make the integrator
                             miss the peak completely and get a bogus
                             answer (although the \"be_very_careful\"
                             option will help here).

  Outputs: (limit, x, y)

    limit -- the limit found.

    x, y -- vector of x and y values of the likelihood function at the
            points used to evaluate the integral. This can be used to
            plot the profile likelihood.
  """  

    # This function has 4 main components:
    #
    # 1) Find the global maximum of the likelihood function using ST
    # 2) Define the integration limits by finding the points at which the
    #    log likelihood has fallen by a certain amount (freezing all other
    #    parameters)
    # 3) Integrate the function using the QUADPACK adaptive integrator
    # 4) Calculate the upper limit by re-integrating the function using
    #    the evaluations made by the adaptive integrator. Two schemes are
    #    tried, splines to the function points and trapezoidal quadrature.

    # Optimizer uses verbosity level one smaller than given here
    optverbose = max(verbose-1, 0)

    ###########################################################################
    #
    # 1) Find the global maximum of the likelihood function using ST
    #
    ###########################################################################

    # Make sure desired parameter is free during global optimization
    src_spectrum = like[srcName].funcs['Spectrum']
    par = src_spectrum.normPar()
    par.setFree(1)
    like.logLike.syncSrcParams(srcName)

    # Perform global optimization
    if verbose:
        print "Finding global maximum"
    try:
        like.fit(optverbose)
    except RuntimeError:
        print "Optimizer failed to find global maximum, results may be wrong"
        pass

    # Store values of global fit
    maxval = like.logLike.value()
    fitval = par.getValue()
    fiterr = par.error()
    limlo, limhi = par.getBounds()
    if verbose:
        print "Maximum of %g with %s = %g +/- %g"\
              %(maxval,srcName,fitval,fiterr)

    # Freeze all other model parameters if requested (much faster!)
    if(freeze_all):
        for i in range(len(like.model.params)):
            if(like[i].srcName != srcName):
                like.model[i].setFree(0)
                like.logLike.syncSrcParams(like[i].srcName)

    all_frozen = True
    for i in range(len(like.model.params)):
        if not like.model[i].isFree():
            all_frozen = False
            break

    ###########################################################################
    #
    # 2) Define the integration limits by finding the points at which the
    #    log likelihood has fallen by a certain amount (freezing all other
    #    parameters)
    #
    ###########################################################################

    # Search to find sensable limits of integration using SciPy Brent
    # method root finder. The tolerance is set based on the lower flux
    # limit - it's not so critical to find the integration limits with
    # high accuaracy, since it they are chosen relatively arbitrarily.

    # 2009-04-16: modified to do logarithmic search before calling
    # Brent because the minimizer does not converge very well when it
    # is called alternatively at extreme ends of the flux range,
    # because the "nuiscence" parameters are very far from their
    # optimal values from call to call.

    nuisance_cache = dict()
    root_cache = dict()
    subval = maxval - delta_log_like_limits
    brent_xtol = limlo*0.1

    xlo = min(fitval*0.1, fitval-(limhi-limlo)*1e-4)
    while(xlo>limlo and\
          _root(xlo,root_cache,like,par,srcName,subval,verbose,
                all_frozen,nuisance_cache)>=0):
        xlo *= 0.1
        pass
    if xlo<limlo: xlo=limlo
    if xlo>limlo or \
           _root(xlo, root_cache,like,par,srcName,subval,verbose,
                 all_frozen,nuisance_cache)<0:
        xlo = scipy.optimize.brentq(_root, xlo, fitval, xtol=brent_xtol,
                                    args = (root_cache,like,par,srcName,\
                                     subval,verbose,all_frozen,nuisance_cache))
        pass

    xhi = max(fitval*10.0, fitval+(limhi-limlo)*1e-4)
    while(xhi<limhi and\
          _root(xhi,root_cache,like,par,srcName,subval,verbose,
                all_frozen,nuisance_cache)>=0):
        xhi *= 10.0
        pass
    if xhi>limhi: xhi=limhi
    if xhi<limhi or \
           _root(xhi, root_cache,like,par,srcName,subval,verbose,
                 all_frozen,nuisance_cache)<0:
        xhi = scipy.optimize.brentq(_root, fitval, xhi, xtol=brent_xtol,
                                    args = (root_cache,like,par,srcName,\
                                     subval,verbose,all_frozen,nuisance_cache))
        pass

    if verbose:
        print "Integration bounds: %g to %g (%d fcn evals)"\
              %(xlo,xhi,len(root_cache))

    ###########################################################################
    #
    # 3) Integrate the function using the QUADPACK adaptive integrator
    #
    ###########################################################################

    #
    # Do integration using QUADPACK routine from SciPy -- the "quad"
    # routine uses adaptive quadrature, which *should* spend more time
    # evaluating the function where it counts the most.
    #
    points = []
    epsrel = (1.0-ul)*1e-3
    if be_very_careful:
        # In "be very careful" mode we use a tighter tolerance value and
        # explicitly tell "quad" that it should examine more carefully
        # the point at x=fitval, which is the peak of the likelihood.
        points = [ fitval ]
        epsrel = (1.0-ul)*1e-8
    
    f_of_x = dict()
    quad_ival, quad_ierr = \
          scipy.integrate.quad(_integrand, xlo, xhi,\
                               args=(f_of_x, like, par, srcName, maxval,\
                                     verbose, all_frozen ,nuisance_cache),\
                               points=points, epsrel=epsrel, epsabs=1)

    if verbose:
        print "Total integral: %g +/- %g (%d fcn evals)"\
              %(quad_ival,quad_ierr,len(f_of_x))

    ###########################################################################
    #
    # 4) Calculate the upper limit by re-integrating the function using
    #    the evaluations made by the adaptive integrator. Two schemes are
    #    tried, splines to the function points and trapezoidal quadrature.
    #
    ###########################################################################

    # Calculation of the upper limit requires integrating up to
    # various test points, and finding the one that contains the
    # prescribed fraction of the probability. Using the "quad"
    # function to do this by evaluating the likelihood function
    # directly would be computationally prohibitive, it is preferable
    # to use the function evaluations that have been saved in the
    # "f_of_x" variable.

    # We try 2 different integration approaches on this data:
    # trapezoidal quadrature and integration of a fitted spline, with
    # the expectation that the spline will be better, but that perhaps
    # the trapezoidal might be more robust if the spline fit goes
    # crazy. The method whose results are closest to those from "quad"
    # is picked to do the search.
    
    # Organize values computed into two vectors x & y
    x = f_of_x.keys();
    x.sort()
    y=[]
    for xi in x: y.append(f_of_x[xi])

    # Redo integral from x,y data using trapezoidal & spline (& Simpson)
    trapz_ival = scipy.integrate.trapz(y,x)
    #simps_ival = scipy.integrate.simps(y,x)
    spl_rep = scipy.interpolate.splrep(x,y,xb=xlo,xe=xhi)
    spl_ival = scipy.interpolate.splint(xlo,xhi,spl_rep)

    # Test which is closest to QUADPACK adaptive method: TRAPZ or SPLINE
    if abs(spl_ival - quad_ival) < abs(trapz_ival - quad_ival):
        # Evaluate upper limit using spline
        if verbose:
            print "Using spline integral: %g (delta=%g)"\
                  %(spl_ival,abs(spl_ival/quad_ival-1))
        yseek = ul*spl_ival;
        # Could use Brent here, but simple binary search is sufficient
        xdelta = 0.5*(xhi-xlo)
        xlim = xlo+xdelta
        ylim = scipy.interpolate.splint(xlo,xlim,spl_rep)
        while xdelta/(xhi-xlo)>1e-8:
            xdelta *= 0.5
            #print xdelta, xlim, ylim, yseek, abs(ylim-yseek)
            if ylim>yseek:
                xlim -= xdelta
            else:
                xlim += xdelta
            ylim = scipy.interpolate.splint(xlo,xlim,spl_rep)
        if verbose:
            print "Spline search: %g (P=%g)"%(xlim,ylim/spl_ival)
    else:
        # Evaluate upper limit using trapezoidal rule
        if verbose:
            print "Using trapezoidal integral: %g (delta=%g)"\
                  %(trapz_ival,abs(trapz_ival/quad_ival-1))
        cint = 0;
        Cint = [ 0 ]
        for i in range(len(x)-1):
            cint = cint + 0.5*(f_of_x[x[i+1]]+f_of_x[x[i]])*(x[i+1]-x[i])
            Cint.append(cint)
        for i in range(len(Cint)):
            Cint[i] /= cint

        # Find point at which integral probability exceeds UL probability
        for i in range(len(x)):
            if(Cint[i]>=ul):
                ilimit = i
                break

        # Linear interpolation to find UL point
        x1 = x[ilimit-1]
        y1 = Cint[ilimit-1]
        x2 = x[ilimit]
        y2 = Cint[ilimit]

        xlim = (ul-y1)/(y2-y1)*(x2-x1)+x1
        if verbose:
            print "Trapezoidal search: %g (P=%g)"%(xlim,ul)

    return xlim, x, y

if __name__ == "__main__":
    import sys

    if(len(sys.argv)>1):
        srcName = sys.argv[1]
    else:
        srcName='1ES_1255+244'
        #srcName='1ES_1218+304'
        #srcName='RX_J0319_8+1845'
        #srcName='PKS_2155-304'

    base='/home/sfegan/Analysis/Glast/Extragalactic/Run2_200MeV/'+srcName+'/'+srcName

    obs = UnbinnedAnalysis.UnbinnedObs(eventFile = base+'_ev_roi.fits',
                      scFile    = '/sps/glast/sfegan/data/FT2.fits',
                      expMap    = base+'_expMap.fits',
                      expCube   = base+'_expCube.fits',
                      irfs      = 'P6_V1_DIFFUSE');

    # By using InteractiveMinuit the program can be customized. There
    # is no need for error estimates here, so do not run "HESSE" and
    # use strategy zero. Also, for increased reliability use MINIMIZE
    # rather than MIGRAD, which allows SIMPLEX to be called if
    # necessary.
    like = UnbinnedAnalysis.UnbinnedAnalysis(obs, base+'_fitmodel_pass2.xml',\
                            'InteractiveMinuit,SET STR 0,MIN 0 $TOL,.q')

    # If you don't have InteractiveMinuit then just use regular Minuit
    #like = UnbinnedAnalysis.UnbinnedAnalysis(obs, base+'_fitmodel_pass2.xml',\
    #                                             'Minuit')

    src_spectrum = like[srcName].funcs['Spectrum']
    par = src_spectrum.getParam("Index")
    if par:
        par.setFree(0)
        par.setValue(-2.0)
        like.logLike.syncSrcParams(srcName)
        
    ul, x, y = calc(like, srcName, verbose=2,
                    be_very_careful=True, freeze_all=False)
#                    be_very_careful=True, freeze_all=True)

    for i in range(len(x)):
        print x[i], y[i]
    
    print "UL: ",ul
