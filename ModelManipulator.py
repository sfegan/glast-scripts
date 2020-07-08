#!/usr/bin/env python

# ModelManipulator - make or alter XML model files
# Stephen Fegan - sfegan@llr.in2p3.fr - 2008-12-28
# $Id$

import xml.dom.minidom
from math import log, acos, cos, sin, log10, floor, sqrt, pi, atan2, floor, fabs, pow
import re

class ModelManipulatorException:
    def __init__(self, message):
        self.message = message
        return
    def __str__(self):
        return self.message


class ModelManipulator:

    def __init__(self, filename = None):
        self.dom = xml.dom.minidom.getDOMImplementation()
        if not filename:
            self.doc = self.dom.createDocument(None, "source_library", None)
            self.lib = self.doc.documentElement
            self.lib.setAttribute("title", "source library")
        else:
            self.doc = xml.dom.minidom.parse(filename)
            self.lib = self.doc.documentElement
            node = self.lib
            while node != self.doc:
                delete_node = None
                if node.nodeType == xml.dom.Node.TEXT_NODE:
                    delete_node = node
                if delete_node == None and node.hasChildNodes():
                    node = node.firstChild
                else:
                    while node != self.doc and node.nextSibling == None:
                        node = node.parentNode
                    if node != self.doc:
                        node = node.nextSibling
                if delete_node != None:
                    delete_node.parentNode.removeChild(delete_node)
        return

    # *************************************************************************
    #
    # Various (static) constants
    #
    # *************************************************************************

    def cDiffuseSource():
        return "DiffuseSource"
    
    cDiffuseSource = staticmethod(cDiffuseSource)

    def cPointSource():
        return "PointSource"

    cPointSource = staticmethod(cPointSource)


    # *************************************************************************
    #
    # Various (static) mathematical functions
    #
    # *************************************************************************

    def fluxScale(flux_value):
        return 10**floor(log10(flux_value)+0.5)

    fluxScale = staticmethod(fluxScale)

    def meanEnergy(emin, emax, index_value):
        x=emax/emin
        if index_value==-2.0:
            eflux = emax*log(x)/(x-1)
        elif index_value==-1.0:
            eflux = emin*(x-1)/log(x)
        else:
            eflux = emin*(index_value+1)/(index_value+2)*\
                    (x**(index_value+2)-1)/(x**(index_value+1)-1)
        return eflux

    meanEnergy = staticmethod(meanEnergy)

    # *************************************************************************
    #
    # Conversion of coordinates back and forth between strings and floats
    #
    # *************************************************************************

    def hmsStringToDeg(str):
        hours   = 0
        mins    = 0
        secs    = 0
        fracs   = 0
        frac10s = 1;

        i = 0
        while i<len(str):
            if str[i]>='0' and str[i]<='9':
                hours=hours*10+(ord(str[i])-ord('0'))
                i += 1
            elif str[i]==':' or str[i]=='h' or str[i]==' ':
                i += 1
                break
            else:
                return None

        while i<len(str):
            if str[i]>='0' and str[i]<='9':
                mins=mins*10+(ord(str[i])-ord('0'))
                i += 1
            elif str[i]==':' or str[i]=='m' or str[i]==' ':
                i += 1
                break
            else:
                return None

        while i<len(str):
            if str[i]>='0' and str[i]<='9':
                secs=secs*10+(ord(str[i])-ord('0'))
                i += 1                
            elif str[i]=='.':
                i += 1
                break
            elif str[i]=='s':
                break
            else:
                return None

        while i<len(str):
            if str[i]>='0' and str[i]<='9':
                fracs=fracs*10+(ord(str[i])-ord('0'))
                i += 1
                frac10s=frac10s*10;
            elif str[i]=='s':
                break;
            else:
                return None;

        hours   = float(hours)
        mins    = float(mins)
        secs    = float(secs)
        fracs   = float(fracs)
        frac10s = float(frac10s)

        return 15.0*(hours+(mins + (secs + fracs/frac10s)/60.0)/60.0)

    hmsStringToDeg = staticmethod(hmsStringToDeg)

    def dmsStringToDeg(str):
        sign    = 1.0;
        degs    = 0
        mins    = 0
        secs    = 0
        fracs   = 0
        frac10s = 1;

        if len(str) == 0:
            return None

        i = 0
        if str[i]=='-':
            sign = -1.0
            i += 1
        elif str[i]=='+':
            i += 1

        while i<len(str):
            if str[i]>='0' and str[i]<='9':
                degs=degs*10+(ord(str[i])-ord('0'))
                i += 1
            elif str[i]==':' or str[i]=='h' or str[i]==' ':
                i += 1
                break
            else:
                return None

        while i<len(str):
            if str[i]>='0' and str[i]<='9':
                mins=mins*10+(ord(str[i])-ord('0'))
                i += 1
            elif str[i]==':' or str[i]=='m' or str[i]==' ':
                i += 1
                break
            else:
                return None

        while i<len(str):
            if str[i]>='0' and str[i]<='9':
                secs=secs*10+(ord(str[i])-ord('0'))
                i += 1
            elif str[i]=='.':
                i += 1
                break
            elif str[i]=='s':
                break
            else:
                return None

        while i<len(str):
            if str[i]>='0' and str[i]<='9':
                fracs=fracs*10+(ord(str[i])-ord('0'))
                i += 1
                frac10s=frac10s*10;
            elif str[i]=='s':
                break;
            else:
                return None;

        sign    = float(sign) 
        degs    = float(degs) 
        mins    = float(mins)
        secs    = float(secs)
        fracs   = float(fracs)
        frac10s = float(frac10s)

        return sign*(degs+(mins + (secs + fracs/frac10s)/60.0)/60.0)

    dmsStringToDeg = staticmethod(dmsStringToDeg)

    def degToHMSString(deg, sec_digits=1, hmssep=False, nosep=False):
        multiplier = 1
        idigit = sec_digits
        while idigit>0:
            multiplier *= 10
            idigit -= 1
        ideg = floor(deg*multiplier*3600.0/15.0)
        h=ideg/(60*60*multiplier);
        m=(ideg/(60*multiplier))%60;
        s=(ideg/multiplier)%60;
        f=ideg%multiplier;
        hsep = msep = ':'
        if nosep: 
            hsep = ''
            msep = ''           
        elif hmssep:
            hsep = 'h'
            msep = 'm'
        str = '%02d%s%02d%s%02d'%(h,hsep,m,msep,s)
        if sec_digits>0:
            fmt='.%%0%dd'%sec_digits
            str += (fmt%f)
        if not nosep and hmssep:
            str += 's'

        return str;

    degToHMSString = staticmethod(degToHMSString)

    def degToDMSString(deg, sec_digits=1, dmssep=False, nosep=False):
        multiplier = 1
        idigit = sec_digits
        while idigit>0:
            multiplier *= 10
            idigit -= 1
        ideg = floor(fabs(deg)*multiplier*3600.0)
        x='+';
        if deg<0:
            x='-'
        d=ideg/(60*60*multiplier);
        m=(ideg/(60*multiplier))%60;
        s=(ideg/multiplier)%60;
        f=ideg%multiplier;
        dsep = msep = ':'
        if nosep: 
            dsep = ''
            msep = ''           
        elif dmssep:
            dsep = 'd'
            msep = 'm'
        str = '%s%02d%s%02d%s%02d'%(x,d,dsep,m,msep,s)
        if sec_digits>0:
            fmt='.%%0%dd'%sec_digits
            str += (fmt%f)
        if not nosep and dmssep:
            str += 's'

        return str;

    degToDMSString = staticmethod(degToDMSString)

    # *************************************************************************
    #
    # Angular functions
    #
    # *************************************************************************

    def angsep(ra0, dec0, ra1, dec1):
        '''Return the angular separation between two objects. Use the
        special case of the Vincenty formula that is accurate for all
        distances'''
        C = pi/180
        d0 = C*dec0
        d1 = C*dec1
        r12 = C*(ra0-ra1)
        cd0 = cos(d0)
        sd0 = sin(d0)
        cd1 = cos(d1)
        sd1 = sin(d1)
        cr12 = cos(r12)
        sr12 = sin(r12)
        num = sqrt((cd0*sr12)**2 + (cd1*sd0-sd1*cd0*cr12)**2)
        den = sd0*sd1+cd0*cd1*cr12
        return atan2(num,den)/C

    angsep = staticmethod(angsep)

    def isInROI(ra0, dec0, ra1, dec1, radius_o, radius_i=0):
        a = ModelManipulator.angsep(ra0, dec0, ra1, dec1)
        return a<radius_o and a>=radius_i

    isInROI = staticmethod(isInROI)
    
    # *************************************************************************
    #
    # Internal functions to generate new XML nodes from which source
    # definitions are comprised
    #
    # *************************************************************************

    def parameterFormat(k):
        F = { 'name': '%s', 'free': '%d' }
        f = '%s'
        if k in F:
            f = F[k]
        return f        
    
    parameterFormat = staticmethod(parameterFormat)

    def formatParameter(k, v):
        return ModelManipulator.parameterFormat(k)%v

    formatParameter = staticmethod(formatParameter)

    def setParameterAttributes(param, name, free, value, scale, min, max):
        param.setAttribute('name',name)
        param.setAttribute('free','%d'%free)
        param.setAttribute('scale','%g'%scale)
        param.setAttribute('value','%g'%value)
        param.setAttribute('max','%g'%max)
        param.setAttribute('min','%g'%min)
        return True

    setParameterAttributes = staticmethod(setParameterAttributes)

    def setParameterAttributesData(param, data):
        for k in data:
            param.setAttribute(k, ModelManipulator.formatParameter(k, data[k]))
        return True

    setParameterAttributesData = staticmethod(setParameterAttributesData)

    def newNodeParameter(self, name, free, value, scale, min, max, P = None):
        if(value<min or value>max):
            raise ModelManipulatorException('Model parameter out of bounds: %g (%g <= %s <= %g)'%(value,min,name,max))
        param = self.doc.createElement('parameter')
        self.setParameterAttributes(param, name, free, value, scale, min, max)
        if P:
            P.appendChild(param)
        return param

    def newNodeParameterData(self, data, P = None):
        if not 'name' in data or not 'free' in data or not 'scale' in data or \
           not 'value' in data or not 'min' in data or not 'max' in data:
            raise ModelManipulatorException('Model parameter data does not contain required values')
        if(data['value']<data['min'] or data['value']>data['max']):
            raise ModelManipulatorException('Model parameter out of bounds: %g (%g <= %s <= %g)'%(data['value'],data['min'],data['name'],data['max']))
        param = self.doc.createElement('parameter')
        self.setParameterAttributes(param, data)
        if P:
            P.appendChild(param)
        return param
    
    def newNodeSpatialModelPS(self, ra, dec, P = None):
        spatial = self.doc.createElement('spatialModel')
        spatial.setAttribute('type','SkyDirFunction')
        self.newNodeParameter('RA',0,ra,1.0,-360.0,360.0, spatial)
        self.newNodeParameter('DEC',0,dec,1.0,-90.0,90.0, spatial)
        if P:
            P.appendChild(spatial)
        return spatial

    def newNodeSpatialModelCV(self, P = None):
        spatial = self.doc.createElement('spatialModel')
        spatial.setAttribute('type','ConstantValue')
        self.newNodeParameter('Value',0,1.0,1.0,0.0,10.0,spatial)
        if P:
            P.appendChild(spatial)
        return spatial

    def newNodeSpatialModelMapCube(self, file, P = None):
        spatial = self.doc.createElement('spatialModel')
        spatial.setAttribute('type','MapCubeFunction')
        spatial.setAttribute('file',file)
        self.newNodeParameter('Normalization', 0, 1, 1, 0.001, 1000, spatial)
        if P:
            P.appendChild(spatial)
        return spatial

    def newNodeSpectrumCV(self, free, value, scale, min, max, P = None):
        spectrum = self.doc.createElement('spectrum')
        spectrum.setAttribute('type','ConstantValue')
        if scale == 0:
            scale=self.fluxScale(value)
        value /= scale
        min /= scale
        max /= scale
        self.newNodeParameter('Value', free, value, scale, min, max, spectrum)
        if P:
            P.appendChild(spectrum)
        return spectrum

    def newNodeSpectrumPL1(self, emin, emax, eflux,
                        flux_free, flux_value, flux_scale, flux_min, flux_max,
                        index_free, index_value, index_min, index_max,
                        P = None):
        elim_min = 30
        elim_max = 300000
        if emin<elim_min:
            elim_min = emin
        if emax>elim_max:
            elim_max = emax 
        # If we are not told what eflux is (the reference energy for the
        # PL) then set it to be the mean for the PL with index of
        # index_value and rescale the flux_value to make it consistent
        if eflux == 0:
            eflux = self.meanEnergy(emin,emax,index_value)
            flux_value *= (eflux/100.0)**index_value
            flux_min *= (eflux/100.0)**index_value
            flux_max *= (eflux/100.0)**index_value
        if flux_scale == 0:
            flux_scale=self.fluxScale(flux_value)
        flux_value /= flux_scale
        flux_min /= flux_scale
        flux_max /= flux_scale
        spectrum = self.doc.createElement('spectrum')
        spectrum.setAttribute('type','PowerLaw')
        self.newNodeParameter('Prefactor',
                           flux_free,flux_value,flux_scale,
                           flux_min,flux_max,spectrum)
        self.newNodeParameter('Index',index_free,index_value,1.0,
                           index_min,index_max,spectrum)
        self.newNodeParameter('Scale',0,eflux,1.0,elim_min,elim_max,spectrum)
        if P:
            P.appendChild(spectrum)
        return spectrum

    def newNodeSpectrumPL2(self, emin, emax,
                        flux_free, flux_value, flux_scale, flux_min, flux_max,
                        index_free, index_value, index_min, index_max,
                        P = None):
        elim_min = 30
        elim_max = 300000
        if emin<elim_min:
            elim_min = emin
        if emax>elim_max:
            elim_max = emax
        if flux_scale == 0:
            flux_scale=self.fluxScale(flux_value)
        flux_value /= flux_scale
        flux_min /= flux_scale
        flux_max /= flux_scale
        spectrum = self.doc.createElement('spectrum')
        spectrum.setAttribute('type','PowerLaw2')
        self.newNodeParameter('Integral',
                           flux_free,flux_value,flux_scale,
                           flux_min,flux_max,spectrum)
        self.newNodeParameter('Index',index_free,index_value,1.0,
                           index_min,index_max,spectrum)
        self.newNodeParameter('LowerLimit',0,emin,1.0,
                              elim_min,elim_max,spectrum)
        self.newNodeParameter('UpperLimit',0,emax,1.0,
                              elim_min,elim_max,spectrum)
        if P:
            P.appendChild(spectrum)
        return spectrum

    def newNodeSpectrumLP(self, eflux, flux_value, alpha_value, beta_value,
                          flux_free = True, alpha_free = True, beta_free = True,
                          emin = 30, emax = 300000, eflux_free = False,
                          flux_scale = 0, flux_min = 0.001, flux_max = 1000,
                          flux_minmax_relative = True,
                          alpha_min = -10, alpha_max = 10,
                          beta_min = -10, beta_max = 10, P = None):
        if alpha_free and eflux_free:
            raise ModelManipulatorException('Alpha and reference energy cannot both be free')
        if eflux == 0:
            raise ModelManipulatorException('Reference energy is zero')
        if flux_scale == 0: 
            flux_scale=self.fluxScale(flux_value)
        if flux_minmax_relative:
            flux_min *= flux_value
            flux_max *= flux_value
        flux_value /= flux_scale
        flux_min /= flux_scale
        flux_max /= flux_scale
        if eflux < emin: emin = eflux
        if eflux > emax: emax = eflux
        spectrum = self.doc.createElement('spectrum')
        spectrum.setAttribute('type','LogParabola')
        self.newNodeParameter('norm',
                              flux_free,flux_value,flux_scale,
                              flux_min,flux_max,spectrum)
        self.newNodeParameter('alpha',alpha_free,-alpha_value,1.0,
                              -alpha_max,-alpha_min,spectrum)
        self.newNodeParameter('beta',beta_free,-beta_value,1.0,
                              -beta_max,-beta_min,spectrum)
        self.newNodeParameter('Eb',eflux_free,eflux,1.0,emin,emax,spectrum)
        if P:
            P.appendChild(spectrum)
        return spectrum

    def newNodeSource(self, name, type, append = True):
        src = self.doc.createElement('source')
        src.setAttribute('name',name)
        src.setAttribute('type',type)
        if append:
            self.lib.appendChild(src)
        return src

    def deleteNode(self, src, name):
        dl = []
        node = src.firstChild
        while node != None:
            if node.nodeName == name:
                dl.append(node)
            node = node.nextSibling
        for node in dl:
            src.removeChild(node)
        return

    def deleteNodeSpectrum(self, src):
        return self.deleteNode(src, 'spectrum')

    # *************************************************************************
    #
    # Functions to add various source definitions to the XML file
    #
    # *************************************************************************

    def addGalprop(self, file, free=1, value=1.0, scale=1.0, min=0.0, max=10.0,
                   name = 'GalProp Diffuse'):
        src = self.newNodeSource(name,self.cDiffuseSource())
        self.newNodeSpectrumCV(free, value, scale, min, max, src)
        self.newNodeSpatialModelMapCube(file, src)
        return True

    def addDiffusePL(self, emin=200, emax=100000, eflux=0,
                     flux_free=1, flux_value=1.6e-7, flux_scale=0,
                     flux_min=1e-10, flux_max=1e-2,
                     index_free=1, index_value=-2.1,
                     index_min=-3.5, index_max=-1.0,
                     name="Extragalactic Diffuse"):
        src = self.newNodeSource(name,self.cDiffuseSource())
        self.newNodeSpectrumPL1(emin, emax, eflux,
                             flux_free, flux_value, flux_scale,
                             flux_min, flux_max,
                             index_free, index_value, index_min, index_max,
                             src)
        self.newNodeSpatialModelCV(src)
        return True

    def addPSPowerLaw1(self, name, ra, dec, emin=200, emax=100000, eflux=0,
                       flux_free=1, flux_value=1e-9, flux_scale=0,
                       flux_min=1e-5, flux_max=1000.0,
                       index_free=1, index_value=-2.0,
                       index_min=-5.0, index_max=-0.5):        
        src = self.newNodeSource(name,self.cPointSource())
        self.newNodeSpectrumPL1(emin, emax, eflux,
                             flux_free, flux_value, flux_scale,
                             flux_min, flux_max,
                             index_free, index_value, index_min, index_max,
                             src)
        self.newNodeSpatialModelPS(ra, dec, src)
        return True

    def addPSPowerLaw2(self, name, ra, dec, emin=200, emax=100000,
                       flux_free=1, flux_value=1.6e-6, flux_scale=0,
                       flux_min=1e-5, flux_max=1000.0,
                       index_free=1, index_value=-2.0,
                       index_min=-5.0, index_max=-0.5):
        src = self.newNodeSource(name,self.cPointSource())
        self.newNodeSpectrumPL2(emin, emax,
                             flux_free, flux_value, flux_scale,
                             flux_min, flux_max,
                             index_free, index_value, index_min, index_max,
                             src)
        self.newNodeSpatialModelPS(ra, dec, src)
        return True

    def addPSLogParabola(self, name, ra, dec,
                         eflux = 200, 
                         flux_value = 1e-12, alpha_value = -2.0, beta_value = 0,
                         flux_free = True, alpha_free = True, beta_free = True,
                         emin = 30, emax = 300000, eflux_free = False,
                         flux_scale = 0, flux_min = 0.001, flux_max = 1000,
                         flux_minmax_relative = True,
                         alpha_min = -10, alpha_max = 10,
                         beta_min = -10, beta_max = 10):
        src = self.newNodeSource(name,self.cPointSource())
        self.newNodeSpectrumLP(eflux = eflux, flux_value = flux_value,
                               alpha_value = alpha_value, 
                               beta_value = beta_value,
                               flux_free = flux_free, alpha_free = alpha_free,
                               beta_free = beta_free, emin = emin, emax = emax,
                               eflux_free = eflux_free, flux_scale = flux_scale,
                               flux_min = flux_min, flux_max = flux_max,
                               flux_minmax_relative = flux_minmax_relative,
                               alpha_min = alpha_min, alpha_max = alpha_max,
                               beta_min = beta_min, beta_max = beta_max, 
                               P = src)
        self.newNodeSpatialModelPS(ra, dec, src)
        return True

    def addPSBrokenPowerLaw2(self, name, ra, dec, emin=200, emax=100000,
                             ebreak_free=0, ebreak=0,
                             ebreak_min=0, ebreak_max=0,
                             flux_free=1, flux_value=1.6, flux_scale=1e-6,
                             flux_max=1000.0, flux_min=1e-5,
                             index_lo_free=1, index_lo_value=-2.0,
                             index_lo_min=-5.0, index_lo_max=-1.0,
                             index_hi_free=1, index_hi_value=-2.0,
                             index_hi_min=-5.0, index_hi_max=-1.0):
        src = self.newNodeSource(name,self.cPointSource())
        elim_min = 30
        elim_max = 300000
        if emin<elim_min:
            elim_min = emin
        if emax>elim_max:
            elim_max = emax 
        if ebreak_min == 0:
            ebreak_min = emin
        if ebreak_max == 0:
            ebreak_max = emax
        if ebreak == 0:
            ebreak = sqrt(ebreak_min*ebreak_max)
        spec = self.doc.createElement('spectrum')
        spec.setAttribute('type','BrokenPowerLaw2')
        self.newNodeParameter('Integral',
                     flux_free,flux_value,flux_scale,flux_min,flux_max,spec)
        self.newNodeParameter('Index1',
                     index_lo_free,index_lo_value,1.0,
                     index_lo_min,index_lo_max,spec)
        self.newNodeParameter('Index2',
                     index_hi_free,index_hi_value,1.0,
                     index_hi_min,index_hi_max,spec)
        self.newNodeParameter('BreakValue',
                     ebreak_free,ebreak,1.0,ebreak_min,ebreak_max,spec)
        self.newNodeParameter('LowerLimit',0,emin,1.0,elim_min,elim_max,spec)
        self.newNodeParameter('UpperLimit',0,emax,1.0,elim_min,elim_max,spec)
        src.appendChild(spec)
        self.newNodeSpatialModelPS(ra, dec, src)
        return True

    def addDeepCopyOfSource(self, source):
         src_node = source
         dst_node = self.lib
         while True:
             new_node = self.doc.createElement(src_node.nodeName)
             dst_node.appendChild(new_node)
             dst_node = new_node
             attributes = src_node.attributes
             if attributes != None:
                 for attr in attributes.items():
                     dst_node.setAttribute(attr[0], attr[1])
             if src_node.hasChildNodes():
                 src_node = src_node.firstChild
             else:
                 dst_node = dst_node.parentNode
                 while src_node != source and \
                           src_node.nextSibling == None:
                     src_node = src_node.parentNode
                     dst_node = dst_node.parentNode
                 if src_node == source:
                     break
                 src_node = src_node.nextSibling
         return True

    # *************************************************************************
    #
    # Functions to decode and manipulate individual sources
    #
    # *************************************************************************

    def nodeIsSource(self, node):
        return node.nodeName == "source"

    def sourceAssert(self, source):
        if not self.nodeIsSource():
            raise ModelManipulatorException('Node is not source')
        return True

    def sourceName(self, source):
        return source.getAttribute('name')

    def sourceClass(self, source):
        return source.getAttribute('type')

    def sourceIsDiffuse(self, source):
        return self.sourceClass(source) == self.cDiffuseSource()

    def sourceIsPointSource(self, source):
        return self.sourceClass(source) == self.cPointSource()

    def sourceGetDataSet(self, source, dataset_name):
        node_list = source.getElementsByTagName(dataset_name)
        if node_list.length == 0:
            return None
        return node_list[0]        

    def datasetGetType(self, dataset):
        return dataset.getAttribute('type')

    def datasetGetParameterNames(self, dataset):
        node_list = dataset.getElementsByTagName('parameter')
        param_list = []
        for node in node_list:
            param_list.append(node.getAttribute('name'))
        return param_list

    def datasetGetParameters(self, dataset):
        return dataset.getElementsByTagName('parameter')

    def parameterGetData(self, parameter):
        data = dict()
        if parameter.attributes != None:
            for attr in parameter.attributes.items():
                k = attr[0]
                v = attr[1]
                if k=='name':
                    pass
                elif k=='free':
                    v = float(v)>0.5
                else:
                    v = float(v)
                data[k] = v
        return data

    def datasetGetParametersData(self, dataset):
        node_list = self.datasetGetParameters(dataset)
        parameters_data = []
        for node in node_list:
            parameters_data.append(self.parameterGetData(node))
        return parameters_data

    def datasetGetParameter(self, dataset, parameter_name):
        node_list = self.datasetGetParameters(dataset)
        for node in node_list:
            name = node.getAttribute('name');
            if node.getAttribute('name') == parameter_name:
                return node
        return None
    
    def datasetGetParameterData(self, dataset, parameter_name):
        node = self.datasetGetParameter(dataset, parameter_name)
        if node == None:
            return None
        return self.parameterGetData(node)

    def sourceGetDataSetType(self, source, dataset_name):
        dataset = self.sourceGetDataSet(source, dataset_name)
        if dataset == None:
            return None
        return self.datasetGetType(dataset)

    def sourceGetParameterNames(self, source, dataset_name):
        dataset = self.sourceGetDataSet(source, dataset_name)
        if dataset == None:
            return None
        return self.datasetGetParameterNames(dataset)

    def sourceGetParameters(self, source, dataset_name):
        dataset = self.sourceGetDataSet(source, dataset_name)
        if dataset == None:
            return []
        return self.datasetGetParameters(dataset)

    def sourceGetParametersData(self, source, dataset_name):       
        dataset = self.sourceGetDataSet(source, dataset_name)
        if dataset == None:
            return []
        return self.datasetGetParametersData(dataset)

    def sourceGetParameter(self, source, dataset_name, parameter_name):
        dataset = self.sourceGetDataSet(source, dataset_name)
        if dataset == None:
            return None
        return self.datasetGetParameter(dataset, parameter_name)
    
    def sourceGetParameterData(self, source, dataset_name, parameter_name):
        dataset = self.sourceGetDataSet(source, dataset_name)
        if dataset == None:
            return None
        return self.datasetGetParameterData(dataset, parameter_name)

    def sourceCoordinates(self, source):
        coord_data = self.sourceGetParametersData(source, 'spatialModel')
        ra = False
        dec = False
        for data in coord_data:
            name = data['name']
            value = data['value']*data['scale']
            if(name == "RA"):
                ra = value
            elif (name == "DEC"):
                dec = value
        if ra == False:
            raise ModelManipulatorException('Source does not RA coordinate')
        if dec == False:
            raise ModelManipulatorException('Source does not DEC coordinate')
        return [ra, dec]

    def sourceSpectrum(self, source):
        spectrum = self.sourceGetDataSet(source, "spectrum")
        if spectrum == None:
            return None
        spectrum_type = self.datasetGetType(spectrum)
        spectrum_parm = self.datasetGetParameters(spectrum)
        result = {}
        result['type'] = spectrum_type
        result['raw'] = {}
        result['scaled'] = {}
        result['node'] = {}
        for parameter in spectrum_parm:
            data = self.parameterGetData(parameter)
            result['node'][data['name']] = parameter
            result['raw'][data['name']] = data.copy()
            scale = data['scale']
            for k in data:
                if k in ( 'free', 'name' ):
                    pass
                else:
                    data[k] *= scale
            result['scaled'][data['name']] = data
        return result

    def dataIsAtLimits(self, data, tol = 1e-9, log_space = False):
        value  = data['value']
        max    = data['max']
        min    = data['min']
        if(log_space):
            value = log(value);
            max   = log(max);
            min   = log(min);
        delta  = (max-min)*tol
        return value+delta>max or value-delta<min        

    def parameterIsAtLimits(self, parameter, tol = 1e-9, log_space = False):
        return self.dataIsAtLimits(self.parameterGetData(parameter),tol)

    def datasetIsAtLimits(self, dataset, tol = 1e-9, test_fixed = False):
        node_list = self.datasetGetParameters(dataset)
        for node in node_list:
            data = self.parameterGetData(node)
            if ( test_fixed or data['free'] ) and \
                   self.parameterIsAtLimits(node, tol):
                return True
        return False        

    def spectrumDatasetIsAtLimits(self, dataset, tol = 1e-9,
                                  test_fixed = False):
        node_list = self.datasetGetParameters(dataset)
        for node in node_list:
            data = self.parameterGetData(node)
            log_space = False
            if(data['name'].lower() in\
               ('prefactor','breakvalue','integral','ebreak','value') ):
                log_space = True
            if ( test_fixed or data['free'] ) and \
                   self.parameterIsAtLimits(node, tol, log_space):
                return True
        return False        

    def sourceIsAtSpectrumLimits(self, source, tol = 1e-9, test_fixed = False):
        dataset = self.sourceGetDataSet(source, "spectrum")
        if dataset == None:
            return None
        return self.spectrumDatasetIsAtLimits(dataset, tol, test_fixed)

    def sourceSpectrumIsFrozen(self, source):
        dataset = self.sourceGetDataSet(source, "spectrum")
        if dataset == None:
            return False
        node_list = self.datasetGetParameters(dataset)
        for node in node_list:
            data = self.parameterGetData(node)
            if data['free'] == True:
                return False
        return True

    def parameterSetData(self, parameter, data):
        return self.setParameterAttributesData(parameter, data)

    def datasetSetParameterData(self, dataset, data):
        node = self.datasetGetParameter(dataset, data['name'])
        if node == None:
            return self.newNodeParameterData(data, dataset)
        else:
            return self.setParameterAttributesData(node, data)
        return False
        
    def sourceSetParameterData(self, source, dataset_name, data):
        dataset = self.sourceGetDataSet(source, dataset_name)
        if dataset:
            return self.datasetSetParameterData(dataset, data)
        return False

    def sourceDelete(self, source):
        return source.parentNode.removeChild(source)

    def sourceFreezeParametersByName(self, source, param_names = None,
                                     free = False, dataset_name = "spectrum",
                                     noregex = False):
        data_list = self.sourceGetParametersData(source, dataset_name)
        for data in data_list:
            name = data['name']
            set_data = False
            if param_names == None:
                set_data = True
            elif type(param_names) == str:
                if noregex:
                    if name == param_names:
                        set_data = True
                else:
                    if re.match(param_names+'$', name):
                        set_data = True
            else:
                if noregex:
                    if name in param_names:
                        set_data = True
                else:
                    for re_name in param_names:
                        if re.match(re_name+'$', name):
                            set_data = True
                            break
            if set_data:
                data['free'] = free
                self.sourceSetParameterData(source, dataset_name, data)
        return True

    def sourceChangeEnergyRange(self, source, emin, emax,
                                forceMeanEref = False, forceEref = 0,
                                resetFluxScale = False):
        spectrum = self.sourceSpectrum(source)
        if not spectrum:
            return False
        spectrum_type = spectrum['type']
        if(spectrum['type'] == "ConstantValue"):
            pass
        elif(spectrum['type'] == "FileFunction"):
            pass
        elif(spectrum_type == "PowerLaw"):
            old_eref = spectrum['scaled']['Scale']['value']
            index = spectrum['scaled']['Index']['value']
            
            if forceEref > 0:
                new_eref = forceEref
            elif forceMeanEref:
                new_eref = self.meanEnergy(emin, emax, index_value)
            else:
                new_eref = old_eref

            if new_eref < emin:
                new_eref = emin
            elif new_eref > emax:
                new_eref = emax

            scale = spectrum['raw']['Scale']['scale']
            spectrum['raw']['Scale']['value'] = new_eref/scale
            spectrum['raw']['Scale']['max'] = emax/scale
            spectrum['raw']['Scale']['min'] = emin/scale
            self.setParameterAttributesData(spectrum['node']['Scale'],
                                            spectrum['raw']['Scale'])

            pf_scale = (new_eref/old_eref)**index
            if resetFluxScale:
                fluxscale = pow(10.0,round(log10(pf_scale)))
                spectrum['raw']['Prefactor']['scale'] *= fluxscale
                pf_scale /= fluxscale
            spectrum['raw']['Prefactor']['value'] *= pf_scale
            spectrum['raw']['Prefactor']['min'] *= pf_scale
            spectrum['raw']['Prefactor']['max'] *= pf_scale
            self.setParameterAttributesData(spectrum['node']['Prefactor'],
                                            spectrum['raw']['Prefactor'])
        elif(spectrum_type == "PowerLaw2"):
            index = spectrum['scaled']['Index']['value']
            old_emin = spectrum['scaled']['LowerLimit']['value']
            old_emax = spectrum['scaled']['UpperLimit']['value']

            escaled = emin/spectrum['raw']['LowerLimit']['scale']
            spectrum['raw']['LowerLimit']['value'] = escaled
            if(spectrum['raw']['LowerLimit']['min'] > escaled):
                spectrum['raw']['LowerLimit']['min'] = escaled
            self.setParameterAttributesData(spectrum['node']['LowerLimit'],
                                            spectrum['raw']['LowerLimit'])

            escaled = emax/spectrum['raw']['UpperLimit']['scale']
            spectrum['raw']['UpperLimit']['value'] = escaled
            if(spectrum['raw']['UpperLimit']['max'] < escaled):
                spectrum['raw']['UpperLimit']['max'] = escaled
            self.setParameterAttributesData(spectrum['node']['UpperLimit'],
                                            spectrum['raw']['UpperLimit'])

            gpo = index+1.0
            int_scale = 1.0
            int_scale /= (old_emax/old_emin)**gpo - 1
            int_scale *= (emax/old_emin)**gpo - (emin/old_emin)**gpo
            if resetFluxScale:
                fluxscale = pow(10.0,round(log10(int_scale)))
                spectrum['raw']['Integral']['scale'] *= fluxscale
                int_scale /= fluxscale
            
            spectrum['raw']['Integral']['value'] *= int_scale
            spectrum['raw']['Integral']['min'] *= int_scale
            spectrum['raw']['Integral']['max'] *= int_scale
            self.setParameterAttributesData(spectrum['node']['Integral'],
                                            spectrum['raw']['Integral'])
        else:
            raise ModelManipulatorException('Spectral type "%s" not supported in sourceChangeEnergyRange'%spectrum_type)

        return True

    def refactorSpectrumAsLP(self, source, eflux = 0, 
                             flux_free = True, alpha_free = True,
                             beta_free = True, eflux_free = False):
        spectrum = self.sourceSpectrum(source)
        if not spectrum:
            return False
        spectrum_type = spectrum['type']
        if(spectrum_type == "ConstantValue"):
            return False
        elif(spectrum_type == "FileFunction"):
            return False
        elif(spectrum_type == "PowerLaw"):
            self.deleteNodeSpectrum(source);
            eflux  = spectrum['scaled']['Scale']['value']
            emax   = spectrum['scaled']['Scale']['max']
            emin   = spectrum['scaled']['Scale']['min']
            flux   = spectrum['scaled']['Prefactor']['value']
            fscale = spectrum['scaled']['Prefactor']['scale']
            fmax   = spectrum['scaled']['Prefactor']['max']
            fmin   = spectrum['scaled']['Prefactor']['min']
            index  = spectrum['scaled']['Index']['value']
            imax   = spectrum['scaled']['Index']['max']
            imin   = spectrum['scaled']['Index']['min']
            bmin   = -10
            bmax   = 10
            self.newNodeSpectrumLP(eflux = eflux, flux_value = flux,
                                   alpha_value = index, beta_value = 0,
                                   flux_free = flux_free,
                                   alpha_free = alpha_free,
                                   beta_free = beta_free, 
                                   emin = emin, emax = emax,
                                   eflux_free = eflux_free, 
                                   flux_scale = fscale,
                                   flux_min = fmin, flux_max = fmax,
                                   flux_minmax_relative = False,
                                   alpha_min = imin, alpha_max = imax,
                                   beta_min = bmin, beta_max = b_max, 
                                   P = source)
        elif(spectrum_type == "PowerLaw2"):
            self.deleteNodeSpectrum(source);
            emax   = spectrum['scaled']['UpperLimit']['value']
            emin   = spectrum['scaled']['LowerLimit']['value']
            iflux  = spectrum['scaled']['Integral']['value']
            ifmax  = spectrum['scaled']['Integral']['max']
            ifmin  = spectrum['scaled']['Integral']['min']
            index  = spectrum['scaled']['Index']['value']
            imax   = spectrum['scaled']['Index']['max']
            imin   = spectrum['scaled']['Index']['min']
            if eflux == 0:
                eflux = self.meanEnergy(emin, emax, index)
            gpo = index+1.0
            flux = iflux*gpo/((emax/eflux)**gpo - (emin/eflux)**gpo)/eflux;
            fmin = flux*ifmin/iflux
            fmax = flux*ifmax/iflux
            bmin   = -10
            bmax   = 10
            self.newNodeSpectrumLP(eflux = eflux, flux_value = flux,
                                   alpha_value = index, beta_value = 0,
                                   flux_free = flux_free,
                                   alpha_free = alpha_free,
                                   beta_free = beta_free, 
                                   emin = emin, emax = emax,
                                   eflux_free = eflux_free, 
                                   flux_scale = 0,
                                   flux_min = fmin, flux_max = fmax,
                                   flux_minmax_relative = False,
                                   alpha_min = imin, alpha_max = imax,
                                   beta_min = bmin, beta_max = bmax, 
                                   P = source)
        elif(spectrum_type == "LogParabola"):
            pass
        else:
            raise ModelManipulatorException('refactorSpectrumAsLP: Spectral type "%s" not supported'%spectrum_type)
        
        return True
    
    # *************************************************************************
    #
    # Functions to return list of sources meeting some set of criteria
    #
    # *************************************************************************

    def listAllSources(self):
        sl = []
        node = self.lib.firstChild
        while node != None:
            if self.nodeIsSource(node):
                sl.append(node)
            node = node.nextSibling
        return sl

    def listDiffuseSources(self, base_sl = False):
        if(base_sl == False):
            base_sl = self.listAllSources()
        sl = []
        for node in base_sl:
            if self.sourceIsDiffuse(node):
                sl.append(node)
        return sl

    def listPointSources(self, base_sl = False):
        if(base_sl == False):
            base_sl = self.listAllSources()
        sl = []
        for node in base_sl:
            if self.sourceIsPointSource(node):
                sl.append(node)
        return sl

    def listSourcesAtSpectrumLimits(self, base_sl = False, tol = 1e-9,
                                    test_fixed = False):
        if(base_sl == False):
            base_sl = self.listAllSources()
        sl = []
        for node in base_sl:
            if self.sourceIsAtSpectrumLimits(node, tol, test_fixed):
                sl.append(node)
        return sl

    def listNamedSources(self, re_list, base_sl = False, noregex = False,
                         exclude = False):
        if(base_sl == False):
            base_sl = self.listAllSources()
        sl = []
        for node in base_sl:
            name = self.sourceName(node)
            if re_list == None:
                if exclude == True:
                    sl.append(node)
            elif type(re_list) == str:
                if noregex:
                    if name == re_list:
                        if exclude == False:
                            sl.append(node)
                    elif exclude == True:
                        sl.append(node)
                else:
                    if re.match(re_list+'$', name):
                        if exclude == False:
                            sl.append(node)
                    elif exclude == True:
                        sl.append(node)
            else:
                if noregex:
                    if name in re_list:
                        if exclude == False:
                            sl.append(node)
                    elif exclude == True:
                        sl.append(node)
                else:
                    found = False
                    for re_name in re_list:
                        if re.match(re_name+'$', name):
                            found = True
                            break
                    if found == True:
                        if exclude == False:
                            sl.append(node)
                    elif exclude == True:
                        sl.append(node)
        return sl

    def listROISources(self, ra, dec, radius_outer, radius_inner = 0,
                       base_sl = False):
        if(base_sl == False):
            base_sl = self.listAllSources()
        sl = []
        for node in self.listPointSources(base_sl):
            [ra1, dec1] = self.sourceCoordinates(node)
            if self.isInROI(ra, dec, ra1, dec1, radius_outer, radius_inner):
                sl.append(node)
        return sl

    def listFrozenSources(self, listed_sl, base_sl = False):
        if(base_sl == False):
            base_sl = self.listAllSources()
        sl = []
        for node in base_sl:
            if self.sourceSpectrumIsFrozen(node):
                sl.append(node)
        return sl

    def listUnlistedSources(self, listed_sl, base_sl = False):
        if(base_sl == False):
            base_sl = self.listAllSources()
        sl = []
        for node in base_sl:
            is_listed = False
            for testnode in listed_sl:
                if(testnode == node):
                    is_listed = True
                    break
            if(not is_listed):
                sl.append(node)
        return sl                

    # *************************************************************************
    #
    # Functions to write XML
    #
    # *************************************************************************

    def output(self, filename = None):
        if filename:
            open(filename,'w').write(self.doc.toprettyxml('  '))
        else:
            print self.doc.toprettyxml('  '),

    def __str__(self):
        return self.doc.toprettyxml('  ')

    
if __name__ == "__main__":
    a = ModelManipulator() #'PKS_2155-304_model.xml')
#    a = ModelManipulator()
    a.addGalprop('MyNameIsMichaelCaine')
    a.addDiffusePL()
#    a.addPSPowerLaw2('Hello',10,20)
    a.addPSLogParabola('Hello',10,20)

    for node in a.listAllSources():
        a.addDeepCopyOfSource(node)
        a.sourceFreezeParametersByName(node, ['Index', 'Integral'])

    a.output()

    b = a.listROISources(321.2,-33.98,10)
    print b
    for node in b:
        print a.sourceGetParametersData(node,'spectrum')
        print a.sourceCoordinates(node)
        print node.attributes.items()
