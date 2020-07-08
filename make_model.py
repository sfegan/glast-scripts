#!/usr/bin/env python

# make_model.py - make a model file from a catalog FITS file - new PY version
# Stephen Fegan - sfegan@llr.in2p3.fr - 2008-10-23
# $Id$

import sys, getopt, subprocess, xml.dom.minidom, math, os, time, math

def fluxScale(flux_value):
    return 10**math.floor(math.log10(flux_value)+0.5)

def meanEnergy(emin, emax, index_value):
    x=emax/emin;
    if index_value==-2.0:
        eflux = emax*math.log(x)/(x-1)
    elif index_value==-1.0:
        eflux = emin*(x-1)/math.log(x)
    else:
        eflux = emin*(index_value+1)/(index_value+2)*\
                (x**(index_value+2)-1)/(x**(index_value+1)-1)
    return eflux

def addParameter(el, name, free, value, scale, min, max):
    doc = el.ownerDocument
    param = doc.createElement('parameter')
    param.setAttribute('name',name)
    param.setAttribute('free','%d'%free)
    param.setAttribute('scale','%g'%scale)
    param.setAttribute('value','%g'%value)
    param.setAttribute('max','%g'%max)
    param.setAttribute('min','%g'%min)
    el.appendChild(param)

def addGalprop(lib, file, free=1, value=1.0, scale=1.0, max=10.0, min=1.0,
               name = 'GalProp Diffuse'):
    doc = lib.ownerDocument
    src = doc.createElement('source')
    src.setAttribute('name',name)
    src.setAttribute('type','DiffuseSource')
    spec = doc.createElement('spectrum')
    spec.setAttribute('type','ConstantValue')
    addParameter(spec, 'Value', free, value, scale, min, max)
    src.appendChild(spec)
    spatial = doc.createElement('spatialModel')
    spatial.setAttribute('file',file)
    spatial.setAttribute('type','MapCubeFunction')
    addParameter(spatial, 'Normalization', 0, 1, 1, 0.001, 1000)
    src.appendChild(spatial)
    lib.appendChild(src)

def addDiffusePL_NEW(lib, file, free=1, value=1.0, scale=1.0, max=10.0, min=1.0,
               name = 'EG_v02'):
    doc = lib.ownerDocument
    src = doc.createElement('source')
    src.setAttribute('name',name)
    src.setAttribute('type','DiffuseSource')
    spec = doc.createElement('spectrum')
    spec.setAttribute('file',file)
    spec.setAttribute('type','FileFunction')
    addParameter(spec, 'Normalization', 0, 1, 1, 0.001, 1000)
    src.appendChild(spec)
    spatial = doc.createElement('spatialModel')
    spatial.setAttribute('type','ConstantValue')
    addParameter(spatial,'Value',0,1.0,1.0,0.0,10.0)
    src.appendChild(spatial)
    lib.appendChild(src)

def addDiffusePL(lib, flux_free=1, flux_value=1.6e-7, flux_scale=0,
                 emin=200, emax=100000, eflux=0,
                 flux_max=100.0, flux_min=1e-5,
                 index_free=1, index_value=-2.1,
                 index_min=-3.5, index_max=-1.0,
                 name="Extragalactic Diffuse"):
    elim_min = 30;
    elim_max = 300000;
    if emin<elim_min:
        elim_min = emin
    if emax>elim_max:
        elim_max = emax 
    # If we are not told what eflux is (the reference energy for the
    # PL) then set it to be the mean for the PL with index of
    # index_value and rescale the flux_value to make it consistent
    if eflux == 0:
        eflux = meanEnergy(emin,emax,index_value)
        flux_value *= (eflux/100.0)**index_value
    if flux_scale == 0:
        flux_scale=fluxScale(flux_value)
    flux_value /= flux_scale
    doc = lib.ownerDocument
    src = doc.createElement('source')
    src.setAttribute('name',name)
    src.setAttribute('type','DiffuseSource')
    spec = doc.createElement('spectrum')
    spec.setAttribute('type','PowerLaw')
    addParameter(spec,'Prefactor',
                 flux_free,flux_value,flux_scale,flux_min,flux_max)
    addParameter(spec,'Index',index_free,index_value,1.0,index_min,index_max)
    addParameter(spec,'Scale',0,eflux,1.0,elim_min,elim_max)
    src.appendChild(spec)
    spatial = doc.createElement('spatialModel')
    spatial.setAttribute('type','ConstantValue')
    addParameter(spatial,'Value',0,1.0,1.0,0.0,10.0)
    src.appendChild(spatial)
    lib.appendChild(src)

def addPSPowerLaw1(lib, name, ra, dec, emin=200, emax=100000, eflux=0,
                   flux_free=1, flux_value=1e-9, flux_scale=0,
                   flux_max=1000.0, flux_min=1e-5,
                   index_free=1, index_value=-2.0,
                   index_min=-5.0, index_max=-0.5):
    elim_min = 30;
    elim_max = 300000;
    if emin<elim_min:
        elim_min = emin
    if emax>elim_max:
        elim_max = emax 
    if eflux==0:
        eflux = meanEnergy(emin,emax,index_value)
        flux_value *= (eflux/100.0)**index_value
    if flux_scale == 0:
        flux_scale=fluxScale(flux_value)
    flux_value /= flux_scale        
    doc = lib.ownerDocument
    src = doc.createElement('source')
    src.setAttribute('name',name)
    src.setAttribute('type','PointSource')
    spec = doc.createElement('spectrum')
    spec.setAttribute('type','PowerLaw')
    addParameter(spec,'Prefactor',
                 flux_free,flux_value,flux_scale,flux_min,flux_max)
    addParameter(spec,'Index',index_free,index_value,1.0,index_min,index_max)
    addParameter(spec,'Scale',0,eflux,1.0,elim_min,elim_max)
    src.appendChild(spec)
    spatial = doc.createElement('spatialModel')
    spatial.setAttribute('type','SkyDirFunction')
    addParameter(spatial,'RA',0,ra,1.0,-360.0,360.0)
    addParameter(spatial,'DEC',0,dec,1.0,-90.0,90.0)
    src.appendChild(spatial)
    lib.appendChild(src)

def addPSPowerLaw2(lib, name, ra, dec, emin=200, emax=100000,
                   flux_free=1, flux_value=1.6e-6, flux_scale=0,
                   flux_max=1000.0, flux_min=1e-5,
                   index_free=1, index_value=-2.0,
                   index_min=-5.0, index_max=-0.5):
    elim_min = 30;
    elim_max = 300000;
    if emin<elim_min:
        elim_min = emin
    if emax>elim_max:
        elim_max = emax
    if flux_scale == 0:
        flux_scale=fluxScale(flux_value)
    flux_value /= flux_scale
    doc = lib.ownerDocument
    src = doc.createElement('source')
    src.setAttribute('name',name)
    src.setAttribute('type','PointSource')
    spec = doc.createElement('spectrum')
    spec.setAttribute('type','PowerLaw2')
    addParameter(spec,'Integral',
                 flux_free,flux_value,flux_scale,flux_min,flux_max)
    addParameter(spec,'Index',index_free,index_value,1.0,index_min,index_max)
    addParameter(spec,'LowerLimit',0,emin,1.0,elim_min,elim_max)
    addParameter(spec,'UpperLimit',0,emax,1.0,elim_min,elim_max)
    src.appendChild(spec)
    spatial = doc.createElement('spatialModel')
    spatial.setAttribute('type','SkyDirFunction')
    addParameter(spatial,'RA',0,ra,1.0,-360.0,360.0)
    addParameter(spatial,'DEC',0,dec,1.0,-90.0,90.0)
    src.appendChild(spatial)
    lib.appendChild(src)

def addPSBrokenPowerLaw2(lib, name, ra, dec, emin=200, emax=100000,
                         ebreak_free=0, ebreak=0, ebreak_min=0, ebreak_max=0,
                         flux_free=1, flux_value=1.6, flux_scale=1e-6,
                         flux_max=1000.0, flux_min=1e-5,
                         index_lo_free=1, index_lo_value=-2.0,
                         index_lo_min=-5.0, index_lo_max=-1.0,
                         index_hi_free=1, index_hi_value=-2.0,
                         index_hi_min=-5.0, index_hi_max=-1.0):
    elim_min = 30;
    elim_max = 300000;
    if emin<elim_min:
        elim_min = emin
    if emax>elim_max:
        elim_max = emax 
    if ebreak_min == 0:
        ebreak_min = emin
    if ebreak_max == 0:
        ebreak_max = emax
    if ebreak == 0:
        ebreak = math.sqrt(ebreak_min*ebreak_max)
    doc = lib.ownerDocument
    src = doc.createElement('source')
    src.setAttribute('name',name)
    src.setAttribute('type','PointSource')
    spec = doc.createElement('spectrum')
    spec.setAttribute('type','BrokenPowerLaw2')
    addParameter(spec,'Integral',
                 flux_free,flux_value,flux_scale,flux_min,flux_max)
    addParameter(spec,'Index1',
                 index_lo_free,index_lo_value,1.0,index_lo_min,index_lo_max)
    addParameter(spec,'Index2',
                 index_hi_free,index_hi_value,1.0,index_hi_min,index_hi_max)
    addParameter(spec,'BreakValue',
                 ebreak_free,ebreak,1.0,ebreak_min,ebreak_max)
    addParameter(spec,'LowerLimit',0,emin,1.0,elim_min,elim_max)
    addParameter(spec,'UpperLimit',0,emax,1.0,elim_min,elim_max)
    src.appendChild(spec)
    spatial = doc.createElement('spatialModel')
    spatial.setAttribute('type','SkyDirFunction')
    addParameter(spatial,'RA',0,ra,1.0,-360.0,360.0)
    addParameter(spatial,'DEC',0,dec,1.0,-90.0,90.0)
    src.appendChild(spatial)
    lib.appendChild(src)

def usage(emax, emin, catalog, galprop, r_inner, r_outer, ebreak,
          ebreak_min, ebreak_max, index_lo, index_hi, flux,
          default_flux_pl2, default_flux_pl1):
    print '''Usage: %s [OPTIONS] [RA DEC NAME]

Options:
  -h, --help    Print this message
  -o, --output  Output filename
  --emax        Maximum energy for point sources [%g MeV]
  --emin        Minimum energy for point sources [%g MeV]
  --eflux       For a differential power-law, specify the reference energy.
                A value of zero can be used to signify the mean energy given
                the values of emin, emax and index.
  --ebreak      Break energy for broken-power-law. If this is given
                as zero, the value will be set to the mid-point of the
                search window and fitting is enabled. A negative value
                Enables fitting with the initial guess set to be the
                absolute of the value given [%g MeV]
  --ebreakmin   Minimum for break energy search window. A value of zero
                means that the "emin" should be used [%g MeV]
  --ebreakmax   Maximum for break energy search window. A value of zero
                means that the "emin" should be used [%g MeV]
  --no_galprop  Disable Galprop diffuse moedl
  --no_diff_pl  Disable diffuse power law model
  --galprop     Galprop file to use in model
                [Default: %s]
  --pl          Use integral power-law source spectrum
  --pl2         Use integral power-law source spectrum
  --pl1         Use differential power-law source spectrum
  --bpl         Use integral broken-power-law source spectrum
  --no_catalog  Disable adding of background sources from catalog
  --catalog     FITS file to read source catalog from
                [Default: %s]
  --inner       Inner radius for catalog search [%g deg]
  --outer       Outer radius for catalog search [%g deg]
  --index       Set power-law index [%g]
  --index_lo    Set broken-power-law low-energy index [%g]
  --index_hi    Set broken-power-law high-energy index [%g]
  --flux        Set flux value. Note, the units for an integral and
                differential power-law are different, so be careful. A
                negative or zero value sets the initial value to its
                default, as described below [%g]
  --flux_dflt2  Set the default integral power-law flux value in ph/cm^2/s
                between 100MeV and infinity. The value will be scaled to the
                actual energy range asked for [%g]
  --flux_dflt1  Set the default differential power-law flux value in
                ph/cm^2/s/MeV at the energy given by the "--eflux" option, or
                at 100MeV if this is zero (the flux will be scaled to whatever
                energy "eflux" is calculated to be) [%g]
  --fix_index   Fix index in model
  --fix_flux    Fix flux in model
  
'''%(sys.argv[0], emax, emin, ebreak, ebreak_min, ebreak_max,
     galprop, catalog, r_inner, r_outer, index_lo, index_lo, index_hi, flux,
     default_flux_pl2, default_flux_pl1)

def main():
    emin = 200.0
    emax = 100000.0
    eflux = 0
    ebreak = 0.0
    ebreak_min = 0.0
    ebreak_max = 0.0
    r_inner = 0.3
    r_outer = 10.0
    index_lo = -2.1
    index_hi = -2.1
    flux = 0
    default_flux_pl1 = 1.0e-9
    default_flux_pl2 = 1.0e-6
    fix_index = False
    fix_flux = False
    output = None
    no_galprop = False
    no_diff_pl = False
    no_catalog = False
    catalog = '/sps/hep/glast/users/sfegan/catalogs/gll_pscAugust_GPconv_like.fit'
    galprop = '/sps/hep/glast/users/sfegan/data/mapcube_54_59Xvarh7S.fits'
    spect = "pl2"

    try:
        optspec = ( "help", "output=", "pl", "pl2", "pl1", "bpl",
                    "emin=", "emax=", "eflux", "no_catalog", "catalog=",
                    "no_galprop", "no_diff_pl", "galprop=", "inner=", "outer=",
                    "ebreak=", "ebreakmin=", "ebreakmax=",
                    "index=", "index_lo=", "index_hi=", "flux=",
                    "fix_index", "fix_flux", "flux_dflt2=", "flux_dflt1=" )
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'ho:', optspec)
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage(emax, emin, catalog, galprop, r_inner, r_outer,
              ebreak, ebreak_min, ebreak_max, index_lo, index_hi, flux,
              default_flux_pl1, default_flux_pl2)
        sys.exit(2)
    
    for o, a in opts:
        if o in ("-h", "--help"):
            usage(emax, emin, catalog, galprop, r_inner, r_outer,
                  ebreak, ebreak_min, ebreak_max, index_lo, index_hi, flux,
                  default_flux_pl1, default_flux_pl2)
            sys.exit()
        elif o in ("-o", "--output"):
            output = a
        elif o in ("--emin"):
            emin = float(a)
        elif o in ("--emax"):
            emax = float(a)
        elif o in ("--eflux"):
            eflux = float(a)
        elif o in ("--no_catalog"):
            no_catalog = True
        elif o in ("--catalog"):
            catalog = a
        elif o in ("--no_galprop"):
            no_galprop = True
        elif o in ("--no_diff_pl"):
            no_diff_pl = True
        elif o in ("--galprop"):
            galprop = a
        elif o in ("--pl", "--pl2"):
            spect = "pl2"
        elif o in ("--pl1"):
            spect = "pl1"
        elif o in ("--bpl"):
            spect = "bpl2"
        elif o in ("--inner"):
            r_inner = float(a)
        elif o in ("--outer"):
            r_outer = float(a)
        elif o in ("--ebreak"):
            ebreak = float(a)
        elif o in ("--ebreakmin"):
            ebreak_min = float(a)
        elif o in ("--ebreakmax"):
            ebreak_max = float(a)
        elif o in ("--index="):
            index_lo = float(a)
            index_hi = float(a)
        elif o in ("--index_lo="):
            index_lo = float(a)
        elif o in ("--index_hi="):
            index_hi = float(a)
        elif o in ("--flux="):
            flux = float(a)
        elif o in ("--fix_index"):
            fix_index = True
        elif o in ("--fix_flux"):
            fix_flux = True
        elif o in ("--flux_dflt2"):
            default_flux_pl2 = float(a)
        elif o in ("--flux_dflt1"):            
            default_flux_pl1 = float(a)
        else:
            assert False, "unhandled option"

    domimpl = xml.dom.minidom.getDOMImplementation()

    doc = domimpl.createDocument(None, "source_library", None)

    lib = doc.documentElement
    lib.setAttribute("title", "source library")
    lib.appendChild(doc.createComment('Source library created by %s at %s'%(sys.argv[0],time.asctime())))
#    lib.appendChild(doc.createComment('Source library created for %s by %s at %s'%(os.getlogin(),sys.argv[0],time.asctime())))

    if (not no_galprop) and (galprop):
        addGalprop(lib, galprop)
    if not no_diff_pl:
        addDiffusePL(lib, emin=emin, emax=emax)

    if len(args) < 3:
        print doc.toprettyxml('  ')
        sys.exit(0);

    ra=float(args[0])
    dec=float(args[1])
    name=args[2]

    if spect in ( "pl2" ):
        if flux == 0:
            flux = default_flux_pl2
            if index_lo == -1.0:
                flux *= log(emax/emin)
            else:
                flux *= ((emin/100)**(index_lo+1)-(emax/100)**(index_lo+1))
        addPSPowerLaw2(lib, name, ra, dec, emin, emax,
                       flux_free=not fix_flux, flux_value=flux,
                       index_free=not fix_index, index_value=index_lo)
    elif spect in ( "pl1" ):
        if flux == 0:
            flux = default_flux_pl2
        addPSPowerLaw1(lib, name, ra, dec, emin, emax, eflux=eflux,
                       flux_free=not fix_flux, flux_value=flux,
                       index_free=not fix_index, index_value=index_lo)
    elif spect in ( "bpl2" ):
        addPSBrokenPowerLaw2(lib, name, ra, dec, emin, emax,
                             ebreak_free=(ebreak<=0), ebreak=abs(ebreak),
                             ebreak_min=ebreak_min, ebreak_max=ebreak_max)
    else:
        print "Internal error: unhandled spectrum type",spect
        sys.exit(1)

    if (not no_catalog) and (catalog):
        filter = 'angsep(RA,DEC,%g,%g)<%g && angsep(RA,DEC,%g,%g)>%g'%\
                 (ra,dec,r_outer,ra,dec,r_inner)
    
        for rline in \
             subprocess.Popen(['fdump','%s[1][%s]'%(catalog,filter),
                               'STDOUT',
                               'NickName,RA,DEC,Flux100,Spectral_Index',
                               '-','prhead=no','showunit=no','showrow=no',
                               'showcol=no','pagewidth=256'],
                         stdout=subprocess.PIPE).communicate()[0].splitlines():
            line = rline.strip()
            if not line:
                continue

            bits = line.split()
            gamma = float(bits[4])
            flux = float(bits[3])
            if gamma==-1.0:
                flux *= 1+log(100/300000)
            else:
                flux *= 1+(300000/100)**(gamma+1)
            
            addPSPowerLaw2(lib, bits[0], float(bits[1]), float(bits[2]),
                           emin, emax, index_value=gamma, flux_value=flux)

    if output:
        open(output,'w').write(doc.toprettyxml('  '))
    else:
        print doc.toprettyxml('  '),

main()
