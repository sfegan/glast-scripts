#!/usr/bin/env python

# modelizer.py - program to shamelessly manipulate XML models
# Stephen Fegan - sfegan@llr.in2p3.fr - 2009-02-12
# $Id$

from ModelManipulator import *
import sys, os, getopt

def smallHelp(exitcode = 0):
    print "See '%s -h' for more help"%os.path.basename(sys.argv[0])
    sys.exit(exitcode)
    
def usage(exitcode = 0):
    progname = os.path.basename(sys.argv[0])
    print """usage: %s [options] [xml_file]

Manipulate Fermi XML models. The program can be used to delete model
entries, freeze and free model parameters, add new sources to the
model. The program reads an input XML file (or optionally creates an
empty one), and performs a list of prescribed tasks on it. Tasks are
specified on the command line, and each task can have various options
associated with it, for example restricting it to a subset of the model
entries. By default, most tasks apply to all entries in the model
unless they are restricted.

General options:

xml_file         file name of XML model to read and manipulate. If no input
                 xml_file name is supplied a new (empty) one will be created.

-h,--help        print this message.

-o,--output X    write the XML file to the given filename 'X' after all
                 manipulations have been completed.

-v               be verbose about doing operations.

--edef Elo,Ehi   specify the default energy range for spectra, default
                 is 200 MeV to 100000 MeV

--resetscale     reset flux scale when changing energy range (if necessary)

Adding sources to model:

--add_gp F       add a galprop-like background to the model. The spectrum
                 defaults to a constant value, with one free paramater, but
                 can be modified by a spectrum parameter. The value of X
                 specifies the filename for the model

--add_uniform    add a uniform background to the model. The spectrum defaults
                 to a power law with two free parameters (flux and index), but
                 can be modified by a spectrum parameter.

--add_pt R,D[,N] add a point source to the model. The RA and Dec should be
                 given as the R and D paramaters. Additionally, the name of
                 the source can be given as the N parameter. The spectrum
                 defaults to a power law with two free parameters (flux and
                 index), but can be modified by a spectrum parameter.

Specifying the name and spectra of added models:

--addname N      specify the name of the source being added

--cv F[,Fmin,Fmax]

                 specify a ConstantValue spectrum with flux given by F. If
                 either F is prepended with an"@" symbol the parameters are
                 fixed. The lower and upper ranges for the F search can also
                 be specified, either directly as a number or as a multiple of
                 the flux by prefixing with an "x".

--pl1 F,I[,Eref,Fmin,Fmax,Imin,Imax]

                 specify a PowerLaw1 spectrum with flux and index as given
                 by F and I. If either F or I are prepended with an "@" symbol
                 the parameters are fixed. The reference energy, and lower and
                 upper ranges for the F and I search can also be specified,
                 either directly as a number or as a multiple of the flux by
                 prefixing with an "x".

--pl2 F,I[,Emin,Emax,Fmin,Fmax,Imin,Imax]

                 specify a PowerLaw2 spectrum with flux and index as given
                 by F and I. If either F or I are prepended with an "@" symbol
                 the parameters are fixed. The reference energy, and lower and
                 upper ranges for the F and I search can also be specified,
                 either directly as a number or as a multiple of the flux by
                 prefixing with an "x".

--lp F,a,b[,Eref,Fmin,Fmax,amin,amax,bmin,bmax]

                 specify a LogParabola spectrum with flux, alpha and beta given
                 by F, a and b. If either of these are prepended with an "@"
                 symbol the parameters are fixed. The reference energy, and 
                 lower and upper ranges for the search can also be specified,
                 either directly as a number or as a multiple of the flux by
                 prefixing with an "x".

Specifying tasks:

--list           simply list the names of all entries matching. It is possibly
                 useful to to use '-o /dev/null' to suppress the output of the
                 XML file so that these can be seen easily.

--ds9 F          export source list to DS9 region file F

--delete         delete sources.

--freeze         freeze parameters of the spectrum.

--free           free parameters of the spectrum.

--erange L,H     reset energy range to L <= E <= H [MeV].

--import F       import sources from another XML file, F.

--spectrum       change the spectral type of the source(s).

Restricting tasks to certain model entries:

--name X[,X...]  apply tasks to entries whose names exactly match one of those
                 given in the list.

--regex X[,X...] apply tasks to entries whose names match one of the regular
                 expressions given, for example '--regex ASO.\*'.

--excludename X[,X...]

                 exclude entries whose names exactly match one of those given
                 in the list

--excluderegex X[,X...]

                 exclude entries whose names match one of the regular
                 expressions given, for example '--excluderegex ASO.\*'.

--roi R,D,O[,I]  apply tasks to entries within a donut shaped region of
                 interest centered on RA=R, Dec=D, with outer radius O [deg]
                 and an optional inner radius of I [deg, defaults to zero].

--srcroi X,O,[I] apply tasks to entries within a donut shaped region of
                 interest centered around some (point!) source in the XML
                 file, specified by X. Parameters O and I as above.
                
--diffuse        apply task to diffuse sources only.

--point          apply task to point sources only.

--frozen         apply task to sources with all parameters frozen

--invert         invert selection, so that entries in the XML file that do not
                 match the set of restrictions given (so far) are operated on.

--limited        apply tasks to sources with spectra near the limits.

These options can be cascaded, so '--name 1ES_0033+220' will match the entry
whose name is '1ES_0033+220', while '--name 1ES_0033+220 --invert' will select
all sources whose names are not '1ES_0033+220'. As a final example,
'--name 1ES_0033+220 --invert --srcroi 1ES_0033+220,5' selects all sources
whose names are not '1ES_0033+220' which lie within 5 degrees of '1ES_0033+220'
"""%progname
    sys.exit(exitcode)

def assertFiltersAccepted(filters_accepted):
    if not filters_accepted:
        print 'Filter specification can only be given after a "task" command'
        smallHelp(0)

def assertSpectrumAccepted(spectrum_accepted):
    if not spectrum_accepted:
        print 'Spectrum specification can only be given after a "new source" command'
        smallHelp(0)

def newManip(manipulations, build, type):
    if build:
        manipulations.append(build)
    build = dict();
    build['filt'] = []
    build['type'] = type
    return build

def isFloat(S):
    R = False
    try:
        float(S)
        R = True
    finally:
        return R

def getValueAndFree(str, opt, par):
    value_free = True
    if str and str[0] == '@':
        str = str[1:]
        value_free = False
    if not isFloat(str):
        print "option %s requires requires number for parameter: %s"%(opt,par)
        smallHelp(0)
    return value_free, float(str)

def getScaledValue(str, value, opt, par):
    scale = False
    if str and str[0] == 'x':
        str = str[1:]
        scale = True
    if not isFloat(str):
        print "option %s requires requires number for parameter: %s"%(opt,par)
        smallHelp(0)
    if scale:
        return float(str)*value
    else:
        return float(str)

def filterSources(M, filter, lookupnames):
    sources = M.listAllSources()
    for f in filter:
#        print f
        if f['type'] == 'name':
            sources = M.listNamedSources(f['names'], sources,
                                         noregex = f['noregex'])
        elif f['type'] == 'exclude':
            sources = M.listNamedSources(f['names'], sources,
                                         noregex = f['noregex'],
                                         exclude = True)
        elif f['type'] == 'roi':
            if 'name' in f:
                f['ra'] = lookupnames[f['name']][0]
                f['dec'] = lookupnames[f['name']][1]
                sources = M.listROISources(f['ra'], f['dec'], f['ro'], f['ri'],
                                           sources)
        elif f['type'] == 'diffuse':
            sources = M.listDiffuseSources(sources)
        elif f['type'] == 'point':
            sources = M.listPointSources(sources)
        elif f['type'] == 'frozen':
            sources = M.listFrozenSources(sources)
        elif f['type'] == 'invert':
            sources = M.listUnlistedSources(sources)
        elif f['type'] == 'limited':
            sources = M.listSourcesAtSpectrumLimits(sources,1e-3)
    return sources

def addSpectrum(M, src, spec, emin, emax):
    if spec['type'] == 'cv':
        assert 'value' in spec and isFloat(spec['value'])

        value       = spec['value']
        value_scale = 0
        value_free  = True
        value_max   = value * 1e3
        value_min   = value * 1e-3
        if 'value_free' in spec:
            value_free = spec['value_free']
        if 'value_scale' in spec:
            value_scale = spec['value_scale']
        if  'value_min' in spec:
            value_min = spec['value_min']
        if  'value_max' in spec:
            value_max = spec['value_max']

        M.newNodeSpectrumCV(value_free, value, value_scale,
                            value_min, value_max, src)
    elif spec['type'] == 'pl1':
        assert 'value' in spec and isFloat(spec['value'])
        assert 'index' in spec and isFloat(spec['index'])

        value       = spec['value']
        value_scale = 0
        value_free  = True
        value_max   = value * 1e3
        value_min   = value * 1e-5
        if 'value_free' in spec:
            value_free = spec['value_free']
        if 'value_scale' in spec:
            value_scale = spec['value_scale']
        if  'value_min' in spec:
            value_min = spec['value_min']
        if  'value_max' in spec:
            value_max = spec['value_max']
        
        index      = spec['index']
        index_free = True
        index_max  = -0.5
        index_min  = -5.0
        if 'index_free' in spec:
            index_free = spec['index_free']
        if  'index_min' in spec:
            index_min = spec['index_min']
        if  'index_max' in spec:
            index_max = spec['index_max']

        eflux = emin
        if  'eref' in spec:
            eflux = spec['eref']

        M.newNodeSpectrumPL1(emin, emax, eflux,
                             value_free, value, value_scale,
                             value_min, value_max,
                             index_free, index, index_min, index_max, src)

    elif spec['type'] == 'pl2':
        assert 'value' in spec and isFloat(spec['value'])
        assert 'index' in spec and isFloat(spec['index'])

        value       = spec['value']
        value_scale = 0
        value_free  = True
        value_max   = value * 1e3
        value_min   = value * 1e-5
        if 'value_free' in spec:
            value_free = spec['value_free']
        if 'value_scale' in spec:
            value_scale = spec['value_scale']
        if  'value_min' in spec:
            value_min = spec['value_min']
        if  'value_max' in spec:
            value_max = spec['value_max']
        
        index      = spec['index']
        index_free = True
        index_max  = -0.5
        index_min  = -5.0
        if 'index_free' in spec:
            index_free = spec['index_free']
        if  'index_min' in spec:
            index_min = spec['index_min']
        if  'index_max' in spec:
            index_max = spec['index_max']

        if  'emin' in spec:
            emin = spec['emin']
        if  'emax' in spec:
            emax = spec['emax']

        M.newNodeSpectrumPL2(emin, emax,
                             value_free, value, value_scale,
                             value_min, value_max,
                             index_free, index, index_min, index_max, src)

    elif spec['type'] == 'lp':
        assert 'value' in spec and isFloat(spec['value'])
        assert 'alpha' in spec and isFloat(spec['alpha'])
        assert 'beta' in spec and isFloat(spec['beta'])

        value       = spec['value']
        value_scale = 0
        value_free  = True
        value_max   = value * 1e3
        value_min   = value * 1e-5
        if 'value_free' in spec:
            value_free = spec['value_free']
        if 'value_scale' in spec:
            value_scale = spec['value_scale']
        if  'value_min' in spec:
            value_min = spec['value_min']
        if  'value_max' in spec:
            value_max = spec['value_max']
        
        alpha      = spec['alpha']
        alpha_free = True
        alpha_max  = 10
        alpha_min  = -10
        if 'alpha_free' in spec:
            alpha_free = spec['alpha_free']
        if  'alpha_min' in spec:
            alpha_min = spec['alpha_min']
        if  'alpha_max' in spec:
            alpha_max = spec['alpha_max']

        beta      = spec['beta']
        beta_free = True
        beta_max  = 10
        beta_min  = -10
        if 'beta_free' in spec:
            beta_free = spec['beta_free']
        if  'beta_min' in spec:
            beta_min = spec['beta_min']
        if  'beta_max' in spec:
            beta_max = spec['beta_max']

        eflux = emin
        if  'eref' in spec:
            eflux = spec['eref']

        M.newNodeSpectrumLP(eflux = eflux, flux_value = value, 
                            alpha_value = alpha, beta_value = beta,
                            flux_free = value_free, alpha_free = alpha_free,
                            beta_free = beta_free, emin = emin, emax = emax,
                            eflux_free = False, flux_scale = value_scale,
                            flux_min = value_min, flux_max = value_max,
                            flux_minmax_relative = False,
                            alpha_min = alpha_min, alpha_max = alpha_max,
                            beta_min = beta_min, beta_max = beta_max,
                            P = src)

def convertSpectrum(M, src, spec, emin, emax):
    if spec['type'] == 'cv':
        pass
    elif spec['type'] == 'pl1':
        pass
    elif spec['type'] == 'pl2':
        pass
    elif spec['type'] == 'lp':
        M.refactorSpectrumAsLP(src)
        pass

def main():
    try:
        optspec = ( 'help', 'output=', 'edef=', 'resetscale',
                    'add_gp=', 'add_uniform', 'add_pt=',
                    'addname=', 'cv=', 'pl1=', 'pl2=', 'lp=',
                    'list', 'ds9=', 'delete', 'freeze', 'free', 'erange=',
                    'import=', 'set_spectrum', 'convert_spectrum',
                    'name=', 'regex=', 'excludename=', 'excluderegex=', 
                    'roi=', 'srcroi=', 'diffuse', 'point',
                    'frozen', 'invert', 'limited' )
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'ho:v', optspec)
    except getopt.GetoptError, err:
        print err
        smallHelp(0)

    output = ''
    manipulations = []
    build = None;
    lookupnames = {}
    verbose = False

    # *************************************************************************
    #
    # Parse options and build list of manipulations and filters
    #
    # *************************************************************************

    filters_accepted = False
    spectrum_accepted = False
    emin = 200
    emax = 100000
    npt = 0
    reset_flux_scale = False

    for o, a in opts:
        if o in ('-h', '--help'):
            usage(0)
        elif o in ('-o', '--output'):
            output = a
        elif o in ('-v'):
            verbose = True
        elif o in ('--edef'):
            elohi = a.split(',')
            if len(elohi) != 2:
                print "option --edef requires two numbers Elo,Eho"
                smallHelp(0)
            if not isFloat(elohi[0]) or not isFloat(elohi[1]):
                print "option --edef requires two numbers Elo,Eho"
                smallHelp(0)
            emin = float(elohi[0])
            emax = float(elohi[1])
        elif o in ('--resetscale'):
            reset_flux_scale = True
        #
        # New sources        
        #
        elif o in ('--add_gp'):
            build = newManip(manipulations, build, 'add_gp')
            build['name'] = 'GalProp Diffuse'
            build['filename'] = a
            build['spec'] = { 'type': 'cv',
                              'value': 1.0, 'value_free': True }
            filters_accepted = False
            spectrum_accepted = True
        elif o in ('--add_uniform'):
            build = newManip(manipulations, build, 'add_uniform')
            build['name'] = 'Extragalactic Diffuse'
            build['spec'] = { 'type': 'pl1',
                              'value': 1.6e-7, 'value_free': True,
                              'index': -2.1, 'index_free': True,
                              'index_min': -3.5, 'index_max': -1.0 }
            filters_accepted = False
            spectrum_accepted = True
        elif o in ('--add_pt'):
            build = newManip(manipulations, build, 'add_pt')
            bits = a.split(',')
            if len(bits)<2:
                print "option %s requires at least two parameters: R, D"%o
                smallHelp(0)
            ra = bits.pop(0)
            dec = bits.pop(0)
            if isFloat(ra):
                ra = float(ra)
            else:
                ra = ModelManipulator.hmsStringToDeg(ra)
            if isFloat(dec):
                dec = float(dec)
            else:
                dec = ModelManipulator.dmsStringToDeg(dec)
            if not ra or not dec:
                print "option %s requires valid RA and Dec"%o
                smallHelp(0)
            build['ra'] = ra
            build['dec'] = dec
            if bits:
                build['name'] = bits.pop(0)
            else:
                build['name'] = 'PTSrc%d'%npt
                npt += 1
            build['spec'] = { 'type': 'pl1',
                              'value': 1e-9, 'value_free': True,
                              'value_min': 1e-14, 'value_max': 1e-6,
                              'index': -2.0, 'index_free': True,
                              'index_min': -5.0, 'index_max': -0.5 }
            filters_accepted = False
            spectrum_accepted = True
        #
        # Modify spectrum of previously added
        #
        elif o in ('--addname'):
            assertSpectrumAccepted(spectrum_accepted)
            build['name'] = a
        elif o in ('--cv'):
            assertSpectrumAccepted(spectrum_accepted)
            bits = a.split(',')
            if len(bits) < 1:
                print "option %s requires at least one number: F"%o
                smallHelp(0)
            value_free, value = getValueAndFree(bits.pop(0), o, 'F')
            spec = { 'type': 'cv', 'value': value, 'value_free': value_free }
            if bits:
                str = bits.pop(0)
                if str:
                    spec['value_min'] = getScaledValue(str, value, o, 'Fmin')
            if bits:
                str = bits.pop(0)
                if str:
                    spec['value_max'] = getScaledValue(str, value, o, 'Fmax')
            build['spec'] = spec

        elif o in ('--pl1'):
            assertSpectrumAccepted(spectrum_accepted)
            bits = a.split(',')
            if len(bits) < 2:
                print "option %s requires at least two numbers: F, I"%o
                smallHelp(0)
            spec = { 'type': 'pl1' }
            if bits:
                value_free, value = getValueAndFree(bits.pop(0), o, 'F')
                spec['value'] = value
                spec['value_free'] = value_free
            if bits:
                index_free, index = getValueAndFree(bits.pop(0), o, 'I')
                spec['index'] = index
                spec['index_free'] = index_free
            if bits:
                str = bits.pop(0)
                if isFloat(str):
                    spec['eref'] = float(str)
            if bits:
                str = bits.pop(0)
                if str:
                    spec['value_min'] = getScaledValue(str, value, o, 'Fmin')
            if bits:
                str = bits.pop(0)
                if str:
                    spec['value_max'] = getScaledValue(str, value, o, 'Fmax')
            if bits:
                str = bits.pop(0)
                if str:
                    spec['index_min'] = getScaledValue(str, index, o, 'Imin')
            if bits:
                str = bits.pop(0)
                if str:
                    spec['index_max'] = getScaledValue(str, index, o, 'Imax')

            build['spec'] = spec
        elif o in ('--pl2'):
            assertSpectrumAccepted(spectrum_accepted)
            bits = a.split(',')
            if len(bits) < 2:
                print "option %s requires at least two numbers: F, I"%o
                smallHelp(0)
            spec = { 'type': 'pl2' }
            if bits:
                value_free, value = getValueAndFree(bits.pop(0), o, 'F')
                spec['value'] = value
                spec['value_free'] = value_free
            if bits:
                index_free, index = getValueAndFree(bits.pop(0), o, 'I')
                spec['index'] = index
                spec['index_free'] = index_free
            if bits:
                str = bits.pop(0)
                if isFloat(str):
                    spec['emin'] = float(str)
            if bits:
                str = bits.pop(0)
                if isFloat(str):
                    spec['emax'] = float(str)
            if bits:
                str = bits.pop(0)
                if str:
                    spec['value_min'] = getScaledValue(str, value, o, 'Fmin')
            if bits:
                str = bits.pop(0)
                if str:
                    spec['value_max'] = getScaledValue(str, value, o, 'Fmax')
            if bits:
                str = bits.pop(0)
                if str:
                    spec['index_min'] = getScaledValue(str, index, o, 'Imin')
            if bits:
                str = bits.pop(0)
                if str:
                    spec['index_max'] = getScaledValue(str, index, o, 'Imax')
            build['spec'] = spec
        elif o in ('--lp'):
            assertSpectrumAccepted(spectrum_accepted)
            bits = a.split(',')
            if len(bits) < 3:
                print "option %s requires at least two numbers: F, a, b"%o
                smallHelp(0)
            spec = { 'type': 'lp' }
            if bits:
                value_free, value = getValueAndFree(bits.pop(0), o, 'F')
                spec['value'] = value
                spec['value_free'] = value_free
            if bits:
                alpha_free, alpha = getValueAndFree(bits.pop(0), o, 'I')
                spec['alpha'] = alpha
                spec['alpha_free'] = alpha_free
            if bits:
                beta_free, beta = getValueAndFree(bits.pop(0), o, 'I')
                spec['beta'] = beta
                spec['beta_free'] = beta_free
            spec = { 'type': 'lp',
                     'value': value, 'value_free': value_free,
                     'alpha': alpha, 'alpha_free': alpha_free,
                     'beta':  beta,  'beta_free':  beta_free }
            if bits:
                str = bits.pop(0)
                if isFloat(str):
                    spec['eref'] = float(str)
            if bits:
                str = bits.pop(0)
                if str:
                    spec['value_min'] = getScaledValue(str, value, o, 'Fmin')
            if bits:
                str = bits.pop(0)
                if str:
                    spec['value_max'] = getScaledValue(str, value, o, 'Fmax')
            if bits:
                str = bits.pop(0)
                if str:
                    spec['alpha_min'] = getScaledValue(str, alpha, o, 'amin')
            if bits:
                str = bits.pop(0)
                if str:
                    spec['alpha_max'] = getScaledValue(str, alpha, o, 'amax')
            if bits:
                str = bits.pop(0)
                if str:
                    spec['beta_min'] = getScaledValue(str, beta, o, 'bmin')
            if bits:
                str = bits.pop(0)
                if str:
                    spec['beta_max'] = getScaledValue(str, beta, o, 'bmax')
            build['spec'] = spec
        #
        # New manipulations
        #
        elif o in ('--list'):
            build = newManip(manipulations, build, 'list')
            filters_accepted = True
            spectrum_accepted = False
        elif o in ('--ds9'):
            build = newManip(manipulations, build, 'ds9')
            build['filename'] = a
            filters_accepted = True
            spectrum_accepted = False
        elif o in ('--delete'):
            build = newManip(manipulations, build, 'delete')
            filters_accepted = True
            spectrum_accepted = False
        elif o in ('--freeze', '--free'):
            build = newManip(manipulations, build, 'freeze')
            build['free'] = (o == '--free')
            filters_accepted = True
            spectrum_accepted = False
        elif o in ('--erange'):
            build = newManip(manipulations, build, 'erange')
            elohi = a.split(',')
            if len(elohi) != 2:
                print "option --erange requires two numbers Elo,Eho"
                smallHelp(0)
            if not isFloat(elohi[0]) or not isFloat(elohi[1]):
                print "option --erange requires two numbers Elo,Eho"
                smallHelp(0)
            build['elo'] = float(elohi[0])
            build['ehi'] = float(elohi[1])
            if(build['elo'] >= build['ehi']):
                print "option --erange requires Ehi > Elo"
                smallHelp(0)
            filters_accepted = True
            spectrum_accepted = False
        elif o in ('--import'):
            build = newManip(manipulations, build, 'import')
            build['filename'] = a
            filters_accepted = True
            spectrum_accepted = False
        elif o in ('--set_spectrum'):
            build = newManip(manipulations, build, 'set_spectrum')
            filters_accepted = True
            spectrum_accepted = True
        elif o in ('--convert_spectrum'):
            build = newManip(manipulations, build, 'convert_spectrum')
            filters_accepted = True
            spectrum_accepted = True
        #
        # New filters
        #
        elif o in ('--name', '--regex'):
            assertFiltersAccepted(filters_accepted)
            filt = { 'type': 'name', 'names': a.split(','),
                     'noregex': (o=='--name')}
            build['filt'].append(filt)
        elif o in ('--excludename', '--excluderegex'):
            assertFiltersAccepted(filters_accepted)
            filt = { 'type': 'exclude', 'names': a.split(','),
                     'noregex': (o=='--excludename')}
            build['filt'].append(filt)
        elif o in ('--roi'):
            assertFiltersAccepted(filters_accepted)
            roi = a.split(',')
            if len(roi)<3:
                print "option --roi requires RA, Dec and outer radius"
                smallHelp(0)
            ra = roi[0]
            dec = roi[1]
            ro = roi[2]
            if isFloat(ra):
                ra = float(ra)
            else:
                ra = ModelManipulator.hmsStringToDeg(ra)
            if isFloat(dec):
                dec = float(dec)
            else:
                dec = ModelManipulator.dmsStringToDeg(dec)
            if not ra or not dec or not isFloat(ro):
                print "option --roi requires valid RA, Dec, and outer radius"
                smallHelp(0)
            ro = float(ro)
            if len(roi)>4:
                print "option --roi requires exactly 3 or 4 arguments"
                smallHelp(0)
            elif len(roi)==4:
                ri = roi[3]
                if isFloat(ri):
                    ri = float(ri)
                else:
                    print "option --roi requires valid inner radius, if used"
                    smallHelp(0)
            else:
                ri = 0.0
            filt = { 'type': 'roi', 'ra': ra, 'dec': dec, 'ri': ri, 'ro': ro }
            build['filt'].append(filt)
        elif o in ('--srcroi'):
            assertFiltersAccepted(filters_accepted)
            roi = a.split(',')
            if len(roi)<2:
                print "option --srcroi requires source name and outer radius"
                smallHelp(0)
            name = roi[0]
            ro = roi[1]
            if not isFloat(ro):
                print "option --srcroi requires valid outer radius"
                smallHelp(0)
            ro = float(ro)
            lookupnames[name] = None
            if len(roi)>3:
                print "option --srcroi requires exactly 2 or 3 arguments"
                smallHelp(0)
            elif len(roi)==3:
                ri = roi[2]
                if isFloat(ri):
                    ri = float(ri)
                else:
                    print "option --srcroi requires valid inner radius, if used"
                    smallHelp(0)
            else:
                ri = 0.0
            filt = { 'type': 'roi', 'name': name, 'ri': ri, 'ro': ro }
            build['filt'].append(filt)
        elif o in ('--diffuse'):
            assertFiltersAccepted(filters_accepted)
            build['filt'].append({'type': 'diffuse'})
        elif o in ('--point'):
            assertFiltersAccepted(filters_accepted)
            build['filt'].append({'type': 'point'})
        elif o in ('--frozen'):
            assertFiltersAccepted(filters_accepted)
            build['filt'].append({'type': 'frozen'})
        elif o in ('--invert'):
            assertFiltersAccepted(filters_accepted)
            build['filt'].append({'type': 'invert'})
        elif o in ('--limited'):
            assertFiltersAccepted(filters_accepted)
            build['filt'].append({'type': 'limited'})

    if build:
        manipulations.append(build)
    build = None

    # *************************************************************************
    #
    # Load the XML file or create an empty one
    #
    # *************************************************************************

    if len(args)>0:
        M = ModelManipulator(args[0])
    else:
        M = ModelManipulator()

    # *************************************************************************
    #
    # Retrieve any required source coordiantes before sources are deleted
    #
    # *************************************************************************

    for src in M.listPointSources():
        name = M.sourceName(src)
        if name in lookupnames:
            lookupnames[name] = M.sourceCoordinates(src)

    for m in manipulations:
        if m['type']=='add_pt':
            if m['name'] in lookupnames:
                lookupnames[m['name']] = [m['ra'], m['dec']]

    for name in lookupnames:
        if not lookupnames[name]:
            print "Coordinates for source %s not found"%name
            smallHelp(0)

    # *************************************************************************
    #
    # Loop over manipulations
    #
    # *************************************************************************

    for m in manipulations:
        if verbose:
            if m['type']=='list':
                print "List:"
            if m['type']=='ds9':
                print "DS9:"
            elif m['type']=='delete':
                print "Delete:"
            elif m['type']=='freeze':
                if m['free']:
                    print "Free:"
                else:
                    print "Freeze:"
            elif m['type']=='erange':
                print "Erange %g -> %g [MeV]:"%(m['elo'],m['ehi'])
            elif m['type']=='import':
                print "Import %s:"%m['filename']
            elif m['type']=='add_gp':
                print "Add GP diffuse: '%s' -> '%s'"%\
                      (m['name'],m['filename'])
            elif m['type']=='add_uniform':
                print "Add uniform diffuse: '%s'"%m['name']
            elif m['type']=='add_pt':
                print "Add point source: '%s' -> %s %s (%g,%g)"%\
                      (m['name'],M.degToHMSString(m['ra']),
                       M.degToDMSString(m['dec']),m['ra'],m['dec'])

        # *********************************************************************
        # Handle add sources
        # *********************************************************************
        if m['type']=='add_gp':
            src = M.newNodeSource(m['name'],M.cDiffuseSource())
            addSpectrum(M, src, m['spec'], emin, emax)
            M.newNodeSpatialModelMapCube(m['filename'], src)
            continue
        elif m['type']=='add_uniform':
            src = M.newNodeSource(m['name'],M.cDiffuseSource())
            addSpectrum(M, src, m['spec'], emin, emax)
            M.newNodeSpatialModelCV(src)
            continue
        elif m['type']=='add_pt':
            src = M.newNodeSource(m['name'],M.cPointSource())
            addSpectrum(M, src, m['spec'], emin, emax)
            M.newNodeSpatialModelPS(m['ra'], m['dec'], src)
            continue
            
        # *********************************************************************
        # Handle import separately
        # *********************************************************************
        if m['type']=='import':
            Mext = ModelManipulator(m['filename'])
            sources = filterSources(Mext, m['filt'], lookupnames)
            for s in sources:
                if verbose:
                    print "--",Mext.sourceName(s)
                M.addDeepCopyOfSource(s)
            continue
        
        # *********************************************************************
        # Use filter to determine what sources to act on
        # *********************************************************************
        sources = filterSources(M, m['filt'], lookupnames)

        # *********************************************************************
        # Loop over sources performing tasks
        # *********************************************************************
        for s in sources:
            if verbose:
                print "--",M.sourceName(s)
            if m['type']=='list':
                if M.sourceIsPointSource(s):
                    ra, dec = M.sourceCoordinates(s)
                    print '%-25s %s %s %7.3f %+6.3f'%\
                    (M.sourceName(s),M.degToHMSString(ra),
                     M.degToDMSString(dec),ra,dec)
                else:
                    print '%-25s %s'%(M.sourceName(s),M.sourceClass(s))
            if m['type']=='ds9':
                if(not 'file' in m):
                    m['file'] = open(m['filename'],'w')
                    m['file'].write('# Region file format: DS9 version 4.1\nglobal color=green dashlist=8 3 width=2 font="helvetica 10 normal" select=1 highlite=1 dash=0 fixed=0 edit=1 move=1 delete=1 include=1 source=1\nfk5\n')
                    pass
                if M.sourceIsPointSource(s):
                    ra, dec = M.sourceCoordinates(s)
                    m['file'].write('circle(%7.3f,%+6.3f,1800") # text={%s}\n'\
                                    %(ra,dec,M.sourceName(s)))
                    pass
                pass
            elif m['type']=='delete':
                M.sourceDelete(s)
            elif m['type']=='freeze':
                M.sourceFreezeParametersByName(s, param_names = None,
                                               free = m['free'],
                                               dataset_name = 'spectrum')
            elif m['type']=='erange':
                M.sourceChangeEnergyRange(s, m['elo'], m['ehi'],
                                          resetFluxScale = reset_flux_scale)
            elif m['type']=='set_spectrum':
                M.deleteNodeSpectrum(s);
                addSpectrum(M, s, m['spec'], emin, emax)
            elif m['type']=='convert_spectrum':
                convertSpectrum(M, s, m['spec'], emin, emax)

    # *************************************************************************
    #
    # Write output XML file
    #
    # *************************************************************************

    if output:
        M.output(output)
    else:
        M.output()

if __name__ == '__main__':
    main()
