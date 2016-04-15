#!/usr/bin/awk -f

# convert_gtlike_model_to_gtobssim.awk
# Stephen Fegan - 2010-04-01 - sfegan@llr.in2p3.fr
#
# Convert the gtlike style XML file into a gtobssim - much of the 
# program is spent parsing the XML itself which AWK does not do 
# especially well.
#
# Reference: http://fermi.gsfc.nasa.gov/ssc/data/analysis/scitools/help/gtobssim.txt
# 
# $Id: convert_gtlike_model_to_gtobssim.awk 1680 2010-04-01 14:37:41Z sfegan $

# Split input file on opening XML bracket
BEGIN {
  RS="<";
  if(emin == 0){ emin=50; }
  if(emax == 0){ emax=100000; }
  source_library="";
  source_name="";
};

# Process all non comment lines starting from first XML bracket
(NR>1)&&(!/^!--/){

  # Discard eveything after closing XLM bracket (and also final / if present)
  gsub("/?[ \t]*?>.*$","");
  # Discard leading spaces
  gsub("^[ \t]*","");

  # Parse line into "words" watching out for quotes and literals
  nword=0;
  nchar=length($0);
  newword="";
  quote=0;
  literal=0;
  for(ichar=0;ichar<nchar;ichar++)
    {
      char=substr($0,ichar+1,1);
      if(literal==1) { newword=newword char; literal=0; }
      else if(char=="\\") { literal=1; }
      else if(quote && char=="\"") { quote=0; }
      else if(quote) { newword=newword char; }
      else if(char=="\""){ quote=1; }
      else if(char==" " || char=="\t" || char=="\n")
	{ if(newword!="") { word[nword]=newword; nword++; newword=""; } }
      else { newword=newword char; }
    }
  if(newword!=""){ word[nword]=newword; nword++; newword=""; }
  
  # Skip empty lines -- should not happen
  if(nword==0)next;

  # Organize XML attributes into array of key-value pairs
  for(i in keyval){ delete keyval[i]; }
  for(iword=1;iword<nword;iword++)
    {
      iequals = match(word[iword],"=");
      if(iequals==0)keyval[word[iword]]="";
      else keyval[substr(word[iword],1,iequals-1)]=	\
	substr(word[iword],iequals+1);
    }

  # Extract the source spectal information from the file and spit out
  # a new XML file in the gtobssim format -- not all source spectral
  # types are supported - only PowerLaw and PowerLaw2 and restricted
  # diffuse types

  element=tolower(word[0]);
  if(element=="source_library")
    {
      source_library = keyval["title"];
      printf("<source_library title=\"%s\">\n",source_library);
    }
  if(element=="/source_library")
    {
      printf("</source_library>\n")
    }
  else if(element=="source")
    {
      source_name = keyval["name"];
      source_type = keyval["type"];
      spec_type = "";
      spat_type = "";
      spec_entity = 0;
      spat_entity = 0;
    }
   else if(element=="/source")
    {
      source_flux = -1;
      source_spec = "";
      if(source_type=="PointSource")
	{
	  if(spec_type == "PowerLaw2")
	    {
	      spec_eref = spec_elo;
	      spec_flux = spec_flux/spec_elo*(spec_index+1)/((spec_ehi/spec_elo)**(spec_index+1)-1);
	      spec_type = "PowerLaw";
	    }
	  
	  if(spec_type == "PowerLaw")
	    {
	      source_flux = spec_flux*spec_eref/(spec_index+1)*((emax/spec_eref)**(spec_index+1) - (emin/spec_eref)**(spec_index+1))*1e4;
	      source_spec = sprintf("   <particle name=\"gamma\">\n    <power_law emin=\"%f\" emax=\"%f\" gamma=\"%f\"/>\n   </particle>\n",emin,emax,spec_index*-1.0);
	    }

          if((source_spec != "")&&(spat_type == "SkyDirFunction"))
	    {
	      source_spec = source_spec sprintf("   <celestial_dir ra=\"%f\" dec=\"%f\"/>\n", spat_ra, spat_dec);
	    }
	}
      else if(source_type=="DiffuseSource")
	{
	  if(spat_type == "MapCubeFunction")
	    {
	      if((spec_type == "PowerLaw")||(spec_type == "ConstantValue"))
		{
		  spat_value = spat_value * spec_flux;
		}

	      if(match("gll_iem_v02.fit",spat_file))
                {
                  spat_value = spat_value*8.296;
                }
              else
                {
                  spat_value = spat_value*8.296;
                }
		
	      source_spec = sprintf("   <SpectrumClass name=\"MapCube\" params=\"%f,%s\"/>\n   <use_spectrum frame=\"galaxy\"/>\n",spat_value,spat_file);
	    }
	    else if((spec_type == "FileFunction")&&
		    (spat_type == "ConstantValue"))
	      {
		spec_value = spat_value * spec_flux;
		
		if(match("isotropic_iem_v02.txt",spec_file))
                  {
                    spec_value = spec_value*5.01;
                    spec_elo = 39.3884;
                    spec_ehi = 403761;
                  }
                else
                  {
                    spec_value = spec_value*5.01;
                    spec_elo = 39.3884;
                    spec_ehi = 403761;
                  }
              
                spec_fits = spec_file;
                sub("[^/]*$","isotropic_allsky.fits",spec_fits);
		source_spec = sprintf("   <SpectrumClass name=\"FileSpectrumMap\" params=\"flux=%f,fitsFile=%s,specFile=%s,emin=%f,emax=%f\"/>\n   <use_spectrum frame=\"galaxy\"/>\n",spec_value,spec_fits,spec_file,spec_elo,spec_ehi);
	      }
		
	}
      spec_type = "";

      if(source_spec != "")
	{
	  gsub("^[0-9]","_&",source_name);
	  gsub("[^[:alnum:]]","_",source_name);
	  printf(" <source name=\"%s\"",source_name);
          if(source_flux>0){ printf(" flux=\"%.4e\"",source_flux); }
          printf(">\n")
	  printf("  <spectrum escale=\"MeV\">\n");
	  printf("%s",source_spec);
	  printf("  </spectrum>\n");
	  printf(" </source>\n");
	}
      source_name = "";
      source_type = "";
    }
  else if(element=="spectrum")
    {
      spec_type = keyval["type"];
      spec_entity = 1;

      if(spec_type == "PowerLaw2")
	{
	  spec_flux = 0;
	  spec_index = 0;
	  spec_elo = 0;
	  spec_ehi = 0;
	}
      else if(spec_type == "PowerLaw")
	{
	  spec_flux = 0;
	  spec_index = 0;
	  spec_eref = 0;
	}
      else if(spec_type == "ConstantValue")
	{
	  spec_flux = 0;
	}
      else if(spec_type == "FileFunction")
	{
	  spec_file = keyval["file"];
	  spec_flux = 0;
	}
    }
  else if(element=="/spectrum")
    {
      spec_entity = 0;
    }
  else if(element=="spatialmodel")
    {
      spat_type = keyval["type"];
      spat_entity = 1;

      if(spat_type == "SkyDirFunction")
	{
	  spat_ra=0;
	  spat_dec=0;
	}
      else if(spat_type == "MapCubeFunction")
	{
	  spat_file = keyval["file"];
	  spat_value = 1;
	}
      else if(spat_type == "ConstantValue")
	{
	  spat_value = 1;
	}
    }
  else if(element=="/spatialmodel")
    {
      spat_entity = 0;
    }
  else if(element=="parameter")
    {
      par_val = keyval["value"]*keyval["scale"];
      par_name = keyval["name"];
      if((spec_entity == 1)&&(spec_type == "PowerLaw2"))
	{
	  if(par_name=="Integral") { spec_flux = par_val; }
	  else if(par_name=="Index") { spec_index = par_val; }
	  else if(par_name=="LowerLimit") { spec_elo = par_val; }
	  else if(par_name=="UpperLimit") { spec_ehi = par_val; }
	}
      else if((spec_entity == 1)&&(spec_type == "PowerLaw"))
	{
	  if(par_name=="Prefactor") { spec_flux = par_val; }
	  else if(par_name=="Index") { spec_index = par_val; }
	  else if(par_name=="Scale") { spec_eref = par_val; }
	}
      else if((spec_entity == 1)&&(spec_type == "ConstantValue"))
	{
	  if(par_name=="Value") { spec_flux = par_val; }
	}
      else if((spec_entity == 1)&&(spec_type == "FileFunction"))
	{
	  if(par_name=="Normalization") { spec_flux = par_val; }
	}
      else if((spat_entity == 1)&&(spat_type == "SkyDirFunction"))
	{
	  if(par_name=="RA") { spat_ra = par_val; }
	  else if(par_name=="DEC") { spat_dec = par_val; }
	}
      else if((spat_entity == 1)&&(spat_type == "MapCubeFunction"))
	{
	  if(par_name=="Normalization") { spat_value = par_val; }
	}
      else if((spat_entity == 1)&&(spat_type == "ConstantValue"))
	{
	  if(par_name=="Value") { spat_value = par_val; }
	}
    }
}
